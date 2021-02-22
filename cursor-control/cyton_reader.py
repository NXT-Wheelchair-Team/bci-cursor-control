from brainflow.board_shim import BoardShim, BoardIds


def main():
    BoardShim.enable_dev_board_logger()
    board = BoardShim(BoardIds.CYTON_BOARD, )


if __name__ == "__main__":
    main()
