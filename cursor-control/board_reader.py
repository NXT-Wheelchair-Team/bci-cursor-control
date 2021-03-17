import logging
import os
import threading
import time
from datetime import datetime as datetime
from typing import List

from brainflow.board_shim import BoardShim, BoardIds, BrainFlowInputParams
from nptyping import NDArray

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

    def _run(self):
        """
        Entry-point for the thread.
        """
        with open(self.file_name, "w") as self.file:
            while True:
                if not self.wrote_header:
                    self._write_header()
                    self.wrote_header = True

                self.file.flush()
                time.sleep(0.1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    board = BoardReader()
    file_write = FileWriter(board)
    with board:  # session is open and stream running within this block
        time.sleep(2.5)
        data = board.pop_board_data()  # pops all available data from buffer
        print(len(data[0]) / 250)  # ~2.5 seconds of data
        time.sleep(3)
        data = board.pop_board_data()
        print(len(data[0]) / 250)  # ~3 seconds of data

    # board session and stream are now closed, but can use same object again
    with board:
        time.sleep(1)
        data = board.pop_board_data()
        print(len(data[0]) / 250)
        print(data)
