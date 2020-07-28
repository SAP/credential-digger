import logging

if __name__ == '__main__':
    import plac
    import sys
    from credentialdigger import download

    commands = {
        'download': download,
    }
    if len(sys.argv) == 1:
        logging.info(msg=('Available commands', ', '.join(commands)))
    command = sys.argv.pop(1)
    sys.argv[0] = 'credentialdigger %s' % command
    if command in commands:
        plac.call(commands[command], sys.argv[1:])
    else:
        available = 'Available: {}'.format(', '.join(commands))
        logging.error(msg=('Unknown command: {}'.format(command), available))
