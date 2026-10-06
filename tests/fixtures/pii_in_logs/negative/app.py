import logging

logging.basicConfig(level=logging.INFO)


def process(request):
    logging.info("request ok %s", request.id)
    print("done")