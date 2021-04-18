# Result processing functions =====================================================================

class ResultProcessors:
    """Functions for taking results of many parsers (such as from `Combinators.chain` or `Combinators.many`) and combining into one result,
    or any other post processing you wish to do on the result of a parser (for use with `Combinators.after`)."""

    def doNothing(rs):
        """Result processor: takes a list of results from multiple parsers and combines them into a single result.\n
        No-op; returns exactly what was given."""
        return rs

    def concat(rs):
        """Result processor: takes a list of results from multiple parsers and combines them into a single result.\n
        Converts results to strings and concatenates them."""
        return ''.join(str(r) for r in rs)

    def take(*indexes):
        """Result processor generator: returns a result processor: ``func(results) -> result``\n
        Ignores all results except those at the given indexes. Result is a tuple, unless only one item is taken."""
        def fromProcTake(rs):
            result = tuple(rs[i] for i in range(len(rs)) if i in indexes)
            if len(result) == 1:
                result = result[0]
            return result
        return fromProcTake

    def print(proc):
        """Result processor generator: returns a result processor: ``func(results) -> result``\n
        Returns a processor that prints the results it recieves before calling a different processor. Useful for debugging."""
        def fromPrint(rs):
            print('Results are:', rs)
            return proc(rs)
        return fromPrint

# Parsers =========================================================================================

class PrimitiveParsers:
    """Parsers that provide basic functions. The starting point to build more complex parsers along with combinators."""

    # Ultra-basic: decides to take a character based on a function on that character.
    # Used for pretty much all the other primitive parsers.
    def byFunc(f):
        """Parser generator: returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Returns a parser that that will parse a single character from the input string according to the function provided. Provided function must
        consume a ``str`` and return a ``bool``."""
        def fromByFunc(string):
            c, rest = string[:1], string[1:]
            if f(c):
                return c, rest
        return fromByFunc

    # Primitives

    def digit(string):
        """Parser: takes a string as an input and returns either ``None`` if the parser failed, or a tuple of the parsed output and the remaining unconsumed input.\n
        Parses a single digit (0-9) from the input string."""
        return PrimitiveParsers.byFunc(lambda c: c.isdigit())(string)

    def letter(string):
        """Parser: takes a string as an input and returns either ``None`` if the parser failed, or a tuple of the parsed output and the remaining unconsumed input.\n
        Parses a single letter (a-z or A-Z) from the input string."""
        return PrimitiveParsers.byFunc(lambda c: c.isalpha())(string)

    def nonWhitespace(string):
        """Parser: takes a string as an input and returns either ``None`` if the parser failed, or a tuple of the parsed output and the remaining unconsumed input.\n
        Parses a single non-whitespace character from the input string."""
        return PrimitiveParsers.byFunc(lambda c: not c.isspace() and c != '')(string)

    def whitespace(string):
        """Parser: takes a string as an input and returns either ``None`` if the parser failed, or a tuple of the parsed output and the remaining unconsumed input.\n
        Parses a single whitespace character from the input string."""
        return PrimitiveParsers.byFunc(lambda c: c.isspace())(string)

    def char(c):
        """Parser generator: returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Returns a parser that that will parse one of the given character from the input string."""
        return PrimitiveParsers.byFunc(lambda ic: ic == c)
    
    def notChar(c):
        """Parser generator: returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Returns a parser that that will parse any character except the given character from the input string."""
        return PrimitiveParsers.byFunc(lambda ic: ic != c and ic != '')

    def take(n):
        """Parser generator: returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Returns a parser that that will parse `n` characters from the input string, whatever they are."""
        def fromTake(string):
            if len(string) >= n:
                return string[:n], string[n:]
        return fromTake


# Combinators

class Combinators:
    def chain(*parsers, proc=ResultProcessors.concat):
        """Parser generator: returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Returns a parser that attempts to runs a list of parsers one at a time, and only succeeds if all of them succeed."""
        def fromChain(string):
            results = ()
            rest = string
            for p in parsers:
                pr = p(rest)
                if pr is not None:
                    result, rest = pr
                    results += (result,)
                else:
                    return None
            if len(results) == 0:
                return None
            return results, rest
        return Combinators.after(fromChain, proc)

    def many(parser, proc=ResultProcessors.concat):
        """Parser generator: returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Returns a parser that runs the same parser over and over until it fails, and returns all results. Fails if it can't parse at
        least once."""
        def fromMany(string):
            results = ()
            pr = parser(string)
            while pr is not None:
                result, rest = pr
                results += (result,)
                pr = parser(rest)
            if len(results) == 0:
                return None
            return results, rest
        return Combinators.after(fromMany, proc)

    def manyOrNone(parser, proc=ResultProcessors.concat):
        """Parser generator: returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Returns a parser that runs the same parser over and over until it fails, and returns all zero or more results."""
        return Combinators.maybe(Combinators.many(parser, proc))

    def maybe(parser):
        """Parser generator: returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Returns a parser that runs one parser and never fails; if the given parser fails, this parser returns an empty string. Otherwise
        returns what the given parser would have."""
        def fromMaybe(string):
            pr = parser(string)
            if pr is None:
                return '', string
            else:
                return pr
        return fromMaybe

    def choice(*parsers):
        """Parser generator: returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Returns a parser that runs through a list of given parsers one at a time until one succeeds, and returns that result. Fails if
        all given parsers fail."""
        def fromChoice(string):
            for p in parsers:
                pr = p(string)
                if pr is not None:
                    return pr
        return fromChoice

    def ignore(parser):
        """Parser generator: returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Returns a parser that runs the given parser, but then returns an empty string, no matter what the given parser did. This still consumes
        the input the given parser did."""
        def fromIgnore(string):
            pr = parser(string)
            if pr is None:
                return '', string
            else:
                return '', pr[1]
        return fromIgnore

    def after(parser, proc):
        """Parser generator: returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Returns a parser that runs a parser, and then runs the given result processor on the result. If either the input parser or the processor
        fail, this parser fails."""
        def fromAfter(string):
            pr = parser(string)
            if pr is not None:
                result, rest = pr
                try:
                    processed = proc(result)
                    if processed is None: return None
                    return processed, rest
                except:
                    return None
        return fromAfter

    def whole(parser):
        """Parser generator: returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Returns a parser that fails if the given parser does not consume the entire input, but otherwise behaves the same as the input parser."""
        def fromWhole(string):
            result = parser(string)
            if result is not None and result[1] == '':
                return result
        return fromWhole
    
    def concludeParser(parser):
        """Parser generator: returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Returns a parser that, uniquely, only returns the result and not the unconsumed input. Used for finishing a large, complex parser, so the end user only recieves the parsed object."""
        def fromConcludeParser(string):
            pr = parser(string)
            if pr is not None:
                return pr[0]
        return fromConcludeParser

# Premade useful parsers

class PrebuiltParsers:
    """Premade parsers composed of other parsers. These are provided for convenience, but also as examples of how to combine parsers together."""

    def restOfLine(string):
        """Parser: takes a string as an input and returns either ``None`` if the parser failed, or a tuple of the parsed output and the remaining unconsumed input.\n
        Consumes all input until and including a newline character, or EOF. This parser is composed as follows::
            Combinators.chain(
                Combinators.manyOrNone(PrimitiveParsers.notChar('\\n')),
                Combinators.maybe(PrimitiveParsers.char('\\n'))
            )"""
        return Combinators.chain(
            Combinators.manyOrNone(PrimitiveParsers.notChar('\n')),
            Combinators.maybe(PrimitiveParsers.char('\n'))
        )(string)
    
    def quotedString(string):
        """Parser: takes a string as an input and returns either ``None`` if the parser failed, or a tuple of the parsed output and the remaining unconsumed input.\n
        Consumes all input within two double quotes, ignoring escaped quotes. This parser is composed as follows::
            Combinators.chain(
                PrimitiveParsers.char('"'),
                Combinators.manyOrNone(Combinators.choice(
                    PrebuiltParsers.prefix('\\\\"'),
                    PrimitiveParsers.notChar('"')
                )),
                PrimitiveParsers.char('"'),

                proc=lambda rs: rs[1].replace('\\\\"', '"')
            )"""
        return Combinators.chain(
            PrimitiveParsers.char('"'),
            Combinators.manyOrNone(Combinators.choice(
                PrebuiltParsers.prefix('\\"'),
                PrimitiveParsers.notChar('"')
            )),
            PrimitiveParsers.char('"'),

            proc=lambda rs: rs[1].replace('\\"', '"')
        )(string)
    
    def singleQuotedString(string):
        """Parser: takes a string as an input and returns either ``None`` if the parser failed, or a tuple of the parsed output and the remaining unconsumed input.\n
        Consumes all input within two single quotes, ignoring escaped quotes. This parser is composed as follows::
            Combinators.chain(
                PrimitiveParsers.char('\\\''),
                Combinators.manyOrNone(Combinators.choice(
                    PrebuiltParsers.prefix('\\\\\\\''),
                    PrimitiveParsers.notChar('\\\'')
                )),
                PrimitiveParsers.char('\\\''),

                proc=lambda rs: rs[1].replace('\\\\\\\', '\\\'')
            )"""
        return Combinators.chain(
            PrimitiveParsers.char('\''),
            Combinators.manyOrNone(Combinators.choice(
                PrebuiltParsers.prefix('\\\''),
                PrimitiveParsers.notChar('\'')
            )),
            PrimitiveParsers.char('\''),

            proc=lambda rs: rs[1].replace('\\\'', '\'')
        )(string)

    def isw(parser):
        """Returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Short for "ignore surrounding whitespace." Returns a parser that ignores all whitespace before and after the input parser, but only
        returns the result of the input parser. This parser is composed as follows::
            Combinators.chain(
                PrebuiltParsers.allWhitespace,
                parser,
                PrebuiltParsers.allWhitespace,
                
                proc = ResultProcessors.take(1)
            )"""
        return Combinators.chain(
            PrebuiltParsers.allWhitespace,
            parser,
            PrebuiltParsers.allWhitespace,
            
            proc = ResultProcessors.take(1)
        )

    def prefix(pre):
        """Returns parser as a function: ``func(string) -> tuple(result, rest) or None``\n
        Returns a parser that consumes and returns the given prefix from the beginning of the input. This parser is composed as follows::
            Combinators.chain(
                *tuple(PrimitiveParsers.char(c) for c in pre),

                proc=ResultProcessors.concat
            )"""
        def fromPrefix(string):
            return Combinators.chain(
                *tuple(PrimitiveParsers.char(c) for c in pre),

                proc=ResultProcessors.concat
            )(string)
        return fromPrefix

    def token(string):
        """Parser: takes a string as an input and returns either ``None`` if the parser failed, or a tuple of the parsed output and the remaining unconsumed input.\n
        Consumes and returns all non-whitespace characters from the beginning of the input. This parser is composed as follows::
            Combinators.many(
                PrimitiveParsers.nonWhitespace
            )"""
        return Combinators.many(PrimitiveParsers.nonWhitespace)(string)

    def allWhitespace(string):
        """Parser: takes a string as an input and returns either ``None`` if the parser failed, or a tuple of the parsed output and the remaining unconsumed input.\n
        Parses as many whitespase characters as possbile. This parser is composed as follows::
            Combinators.manyOrNone(
                PrimitiveParsers.whitespace
            )"""
        return Combinators.manyOrNone(PrimitiveParsers.whitespace)(string)

    def integer(string):
        """Parser: takes a string as an input and returns either ``None`` if the parser failed, or a tuple of the parsed output and the remaining unconsumed input.\n
        Parses an integer. This parser is composed as follows::
            Combinators.chain(
                Combinators.maybe(PrimitiveParsers.char('-')),
                Combinators.many(PrimitiveParsers.digit),

                proc = lambda rs: int(''.join(rs))
            )"""
        return Combinators.chain(
            Combinators.maybe(PrimitiveParsers.char('-')),
            Combinators.many(PrimitiveParsers.digit),

            proc = lambda rs: int(''.join(rs))
        )(string)
    
    def decmial(string):
        """Parser: takes a string as an input and returns either ``None`` if the parser failed, or a tuple of the parsed output and the remaining unconsumed input.\n
        Parses a decimal number (float). This parser is composed as follows::
            Combinators.chain(
                Combinators.maybe(PrimitiveParsers.char('-')),
                Combinators.many(PrimitiveParsers.digit),
                Combinators.maybe(Combinators.chain(
                    PrimitiveParsers.char('.'),
                    Combinators.many(PrimitiveParsers.digit)
                )),

                proc = lambda rs: float(''.join(rs))
            )"""
        return Combinators.chain(
            Combinators.maybe(PrimitiveParsers.char('-')),
            Combinators.many(PrimitiveParsers.digit),
            Combinators.maybe(Combinators.chain(
                PrimitiveParsers.char('.'),
                Combinators.many(PrimitiveParsers.digit)
            )),

            proc = lambda rs: float(''.join(rs))
        )(string)

if __name__ == '__main__':
    def apply(input, parser):
        print(f'Input: \'{input}\' --> Output: {parser(input)}\n')
    
    usersRaw = '''User: (name = "Tony", age=26, desc=  "Some programmer idk")
    User: (name  ="Fred", desc   = "Some really awful \\"youtuber\\" who was popular a long time ago", age = -5)
    User: (age=0, name="?", desc="Wait, who is this?")
    User: (desc="One more just as POC that any order is fine.", name="Barsonald", age=9999)'''

    def makeFieldParser(name, valueParser):
        return Combinators.chain(
            PrebuiltParsers.prefix(name),
            PrebuiltParsers.isw(PrimitiveParsers.char('=')),
            valueParser,

            proc=ResultProcessors.take(0, 2)
        )

    anyFieldParser = PrebuiltParsers.isw(Combinators.chain(
        Combinators.choice(
            makeFieldParser('name', PrebuiltParsers.quotedString),
            makeFieldParser('age', PrebuiltParsers.integer),
            makeFieldParser('desc', PrebuiltParsers.quotedString)
        ),
        PrebuiltParsers.allWhitespace,
        Combinators.maybe(PrimitiveParsers.char(',')),

        proc=ResultProcessors.take(0)
    ))
    
    userParser = Combinators.concludeParser(Combinators.many(
        Combinators.chain(
            PrebuiltParsers.prefix('User: ('),
            Combinators.many(anyFieldParser, proc=ResultProcessors.doNothing),
            PrimitiveParsers.char(')'),
            PrebuiltParsers.restOfLine,
            PrebuiltParsers.allWhitespace,

            proc=lambda rs: {k: v for k, v in rs[1]}
        ),
        proc=ResultProcessors.doNothing
    ))

    users = userParser(usersRaw)
    print(users)
    for u in users:
        print('User:')
        print('  Name:', u['name'])
        print('  Age: ', u['age'])
        print('  Desc:', u['desc'])
