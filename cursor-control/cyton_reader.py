import time

from brainflow.board_shim import BoardShim, BoardIds, BrainFlowInputParams


def main():
    BoardShim.enable_dev_board_logger()
    board_params = BrainFlowInputParams()
    board_params.serial_port = "/dev/ttyUSB0"
    board = BoardShim(BoardIds.CYTON_BOARD, board_params)
    board.prepare_session()

    board.start_stream(
        num_samples=250 * 5
    )  # no block, num samples is length of rolling buffer
    time.sleep(10)
    data = board.get_board_data()
    board.stop_stream()
    board.release_session()

    print(data)
    print(len(data[0]) / 250)


if __name__ == "__main__":
    main()
