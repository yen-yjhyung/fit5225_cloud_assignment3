from model.birdnet_analyzer.utils import runtime_error_handler


@runtime_error_handler
def main():
    import model.birdnet_analyzer.cli as cli
    from model.birdnet_analyzer import segments

    # Parse arguments
    parser = cli.segments_parser()

    args = parser.parse_args()

    segments(**vars(args))
