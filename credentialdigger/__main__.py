import logging

if __name__ == "__main__":
    import plac
    import sys
    from credentialdigger import download, scan

    commands = {'download': download, 'scan': scan}
    available_comamnds = f'{", ".join(commands)}'
    if len(sys.argv) == 1:
        logging.error(
            f'You have not called any command.\n\
            Available commands: {available_comamnds}'
        )
        exit()
    command = sys.argv.pop(1)
    sys.argv[0] = f'credentialdigger {command}'
    if command in commands:
        plac.call(commands[command], sys.argv[1:])
    else:
        logging.error(f'Unknown command: {command}\n'
                      f'Available commands: {available_comamnds}')