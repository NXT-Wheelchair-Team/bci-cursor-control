import time

from brainflow.board_shim import BoardShim, BoardIds, BrainFlowInputParams
from nptyping import NDArray

DEFAULT_CYTON_SERIAL_PORT = "/dev/ttyUSB0"
DEFAULT_CYTON_PARAMS = BrainFlowInputParams()
DEFAULT_CYTON_PARAMS.serial_port = DEFAULT_CYTON_SERIAL_PORT


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

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.board.stop_stream()
        self.board.release_session()


if __name__ == "__main__":
    board = BoardReader()
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
