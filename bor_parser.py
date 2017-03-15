#!/usr/bin/env python3

import sys
import json


class BorSyntaxException(Exception):
    pass


def parse(file):
    lines = Lookahead(iter(file.splitlines()))
    delay = .5

    # parse top of file for flags
    while lines.peek() is not None and lines.peek().startswith('#'):
        line = lines.next()
        if line.startswith('#delay '):
            try:
                delay = float(line[7:].strip())
            except ValueError:
                print('Syntax Error on line: "' + line + '"')
                print('Value cannot be converted to "float"')

    return build_sequence(interpret(file.splitlines()), delay)


def interpret(rows):
    lines = Lookahead(iter(rows))
    pattern = []
    delay = .5

    while lines.peek() is not None:
        line = lines.next()
        if line.startswith('#'):
            continue

        elements = line.split(' ')
        if len(elements) == 4 and elements[0] == 'set':
            pattern.append(build_color(elements[1], elements[2], elements[3]))
        elif elements[0].startswith('sequence') or elements[0].startswith('fade'):
            indented_lines = []
            while lines.peek() is not None and lines.peek().startswith("\t"):
                indented_lines.append(lines.next()[1:])

            if '(' in elements[0] and ')' in elements[0]:
                newdelay = elements[0][elements[0].index('(') + 1:elements[0].index(')')]
                delay = float(newdelay) if newdelay.replace('.', '', 1).isdigit() else delay

            if elements[0].startswith('sequence'):
                    new_elements = build_sequence(interpret(indented_lines), delay)
            else:
                new_elements = build_fade(interpret(indented_lines), delay)
            pattern.append(new_elements)
        else:
            print('Syntax Error on line: "' + line + '"')
            raise BorSyntaxException
    return pattern


def build_color(red, green, blue):
    return {
        'type': 'color',
        'red': int(red),
        'green': int(green),
        'blue': int(blue)
    }


def build_sequence(sequence, delay):
    return {
        "type": "sequence",
        "delay": delay,
        "sequence": sequence
    }


def build_fade(colors, delay):
    stripped = []
    for c in colors:
        stripped.append(c)
    return {
        'type': 'fade',
        'delay': delay,
        'colors': stripped
    }


class Lookahead:
    def __init__(self, iter):
        self.iter = iter
        self.buffer = []

    def __iter__(self):
        return self

    def next(self):
        if self.buffer:
            return self.buffer.pop(0)
        else:
            return next(self.iter)

    def peek(self):
        if len(self.buffer) < 1:
            try:
                self.buffer.append(next(self.iter))
            except StopIteration:
                return None
        return self.buffer[0]

    def lookahead(self, n):
        """Return an item n entries ahead in the iteration."""
        while n >= len(self.buffer):
            try:
                self.buffer.append(next(self.iter))
            except StopIteration:
                return None
        return self.buffer[n]


if __name__ == '__main__' and len(sys.argv) == 3:
    infile = open(sys.argv[1], 'r')
    outfile = open(sys.argv[2], 'w')
    try:
        outfile.write(json.dumps(parse(infile.read())))
    except BorSyntaxException:
        print('Syntax incorrect file not saved.')
