from multiprocessing import current_process

def worker(args, function):
    url, base = args
    return function(url)
