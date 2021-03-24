import logging
import os
import threading
import time
from datetime import datetime as datetime
from typing import List

import numpy
from brainflow.board_shim import (
    BoardShim,
    BoardIds,
    BrainFlowInputParams,
    BrainFlowError,
)
from nptyping import NDArray
from nptyping.array import Array

DEFAULT_CYTON_SERIAL_PORT = "/dev/ttyUSB0"
DEFAULT_CYTON_PARAMS = BrainFlowInputParams()
DEFAULT_CYTON_PARAMS.serial_port = DEFAULT_CYTON_SERIAL_PORT

FILE_DIR = os.path.dirname(os.path.realpath(__file__))


class BoardReader:
    def __init__(
        self,
        board_id: BoardIds = BoardIds.CYTON_BOARD,
        board_params: BrainFlowInputParams = DEFAULT_CYTON_PARAMS,
        enable_dev_logger: bool = True,
        buffer_capacity: int = 250 * 10,
    ):
        if enable_dev_logger:
            BoardShim.enable_dev_board_logger()
        self.board = BoardShim(board_id, board_params)
        self.buffer_capacity = buffer_capacity

    def __enter__(self):
        self.board.prepare_session()
        self.board.start_stream(num_samples=self.buffer_capacity)

    def pop_board_data(self) -> NDArray[float]:
        """
        Removes and returns all available data in the buffer, up to a max defined by `buffer_capacity`
        :return: list of channels, channels are a list of samples which are floats
        """
        return self.board.get_board_data()

    def get_board_data(self, num_samples: int) -> NDArray[float]:
        return self.board.get_current_board_data(num_samples)

    def get_eeg_channels(self) -> List[int]:
        return self.board.get_eeg_channels(self.board.board_id)

    def get_sampling_rate(self) -> int:
        return self.board.get_sampling_rate(self.board.board_id)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.board.stop_stream()
        self.board.release_session()


class FileWriter:
    """
    Responsible for writing data from the board reader to a file.
    Operates within a thread, no interaction necessary after construction.
    """

    WRITE_INTERVAL_S = 0.1

    def __init__(
        self,
        board_reader: BoardReader,
        out_dir: str = os.path.join(FILE_DIR, "..", "data"),
    ):
        self.board_reader = board_reader
        self.thread = threading.Thread(target=self._run, daemon=True)
        file_prefix = f"board-{board.board.get_board_id()}"
        iso_time = datetime.now().isoformat()
        self.file_name = os.path.join(out_dir, f"{file_prefix}-{iso_time}.txt")
        self.wrote_header = False
        self.latest_timestamp = None
        self.timestamp_channel = BoardShim.get_timestamp_channel(
            self.board_reader.board.get_board_id()
        )

        self.thread.start()

    def _write_header(self):
        logging.debug("Writing header to file")
        header = [
            "%CursorControl board reader raw EEG data",
            f"%Number of channels = {len(self.board_reader.get_eeg_channels())}",
            f"%Sample rate = {self.board_reader.get_sampling_rate()}",
            f"%Board = {BoardIds(self.board_reader.board.get_board_id()).name}",
        ]
        self.file.write("\n".join(header))
        self.file.write("\n")

    def _get_index_for_timestamp(self, data: Array, timestamp: float) -> int:
        """
        :return: index of the timestamp in the array, -1 if does not exist in array
        """
        last_data_where: Array = numpy.where(
            data[self.timestamp_channel] == self.latest_timestamp
        )[0]
        last_data_index: int = -1 if len(last_data_where) == 0 else last_data_where[0]
        return last_data_index

    def _write_new_data(self):
        logging.debug("Acquiring new data to write to file")
        try:
            data = self.board_reader.get_board_data(self.board_reader.buffer_capacity)
            if len(data) == 0:
                return
            if self.latest_timestamp is not None:
                last_data_index = self._get_index_for_timestamp(
                    data, self.latest_timestamp
                )
                if last_data_index == -1:
                    logging.warning(
                        "Last data no longer in buffer - FileWriter is getting behind and may have lost data"
                    )
                    last_data_index = 0
                new_data_start = last_data_index + 1
                data = data[:, new_data_start:]
            self.latest_timestamp = data[self.timestamp_channel][-1]
            for idx in range(len(data[0])):
                for channel in data:
                    self.file.write(f"{channel[idx]},")
                self.file.write("\n")
        except BrainFlowError as e:
            logging.debug(f"Quietly handling BrainFlowError: {e}")
            return

    def _run(self):
        """
        Entry-point for the thread.
        """
        time.sleep(3)
        with open(self.file_name, "w") as self.file:
            while True:
                if not self.wrote_header:
                    self._write_header()
                    self.wrote_header = True

                self._write_new_data()

                self.file.flush()
                time.sleep(self.WRITE_INTERVAL_S)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    board = BoardReader()
    file_write = FileWriter(board)
    with board:
        while True:  # session is open and stream running within this block
            time.sleep(2.5)
            data = board.get_board_data(int(250 * 2.5))  # gets samples from buffer
            print(len(data[0]) / 250)  # ~2.5 seconds of data
            time.sleep(3)
            data = board.get_board_data(int(250 * 3))
            print(len(data[0]) / 250)  # ~3 seconds of data

    # board session and stream are now closed, but can use same object again
    with board:
        time.sleep(1)
        data = board.get_board_data(int(250 * 1))
        print(len(data[0]) / 250)
        print(data)

    file_write.thread.join()
