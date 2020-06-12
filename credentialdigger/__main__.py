if __name__ == '__main__':
    import plac
    import sys
    from credentialdigger import download

    commands = {
        'download': download,
    }
    if len(sys.argv) == 1:
        print('Available commands', ', '.join(commands))
    command = sys.argv.pop(1)
    sys.argv[0] = 'credentialdigger %s' % command
    if command in commands:
        plac.call(commands[command], sys.argv[1:])
    else:
        available = 'Available: {}'.format(', '.join(commands))
        print('Unknown command: {}'.format(command), available)
