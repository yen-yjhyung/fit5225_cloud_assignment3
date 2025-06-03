import model.birdnet_analyzer.utils as utils


@utils.runtime_error_handler
def main():
    import model.birdnet_analyzer.cli as cli
    from model.birdnet_analyzer import search

    parser = cli.search_parser()
    args = parser.parse_args()

    search(**vars(args))
