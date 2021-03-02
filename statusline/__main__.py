#!/usr/bin/python3
from statusline.status import DirectoryMinify

def main():
    """Run statusline."""
    print(DirectoryMinify().get_statusline())

if __name__ == '__main__':
    main()
