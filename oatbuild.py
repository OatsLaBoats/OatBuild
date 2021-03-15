# Step 1: Read file and tokenize it. DONE
# Step 2: Parse tokens. DONE
# Step 3: Create command. DONE
# Step 4: Run command.
#
# Syntax:
#   Command("parameters")
# 
# Command List:
#   SetProjectName(x) -> projectName
#   SetCompiler(x) -> gcc/cl/clang/clang-cl
#   SetLanguageVersion(x) -> c89/c99/c11/c17
#   SetTargetArch(x) -> 32/64
#   SetOutputType(x) -> shared/object/executable
#   SetBuildType(x) -> debug/release
#   AddFile(...) -> filename1, filename2
#   AddSourcePath(...) -> directory1, directory2
#   AddConstant(...) -> constant1=1, constant2=2
#   AddIncludePath(...) -> path1, path2
#   AddLibrary(...) -> library1, library2
#   AddObjectFile(...) -> object1, object2
#   AddCompilerFlag(...) -> flag1, flag2
#   AddLinkerFlag(...) -> flag1, flag2

import sys
import platform
import os
import time
from enum import Enum

class TokenType(Enum):
    STRING = 1
    LEFT_PAREN = 2
    RIGHT_PAREN = 3
    COMMA = 4
    LINE_END = 5


class Token:
    def __init__(self, tokenType: int, lexeme: str, line: int):
        self.tokenType = tokenType
        self.lexeme = lexeme
        self.line = line

    def print(self) -> None:
        print(f"[{self.line}]", end = " ")

        if self.tokenType == TokenType.STRING:
            print("     STRING", end = " ")
        elif self.tokenType == TokenType.LEFT_PAREN:
            print(" LEFT_PAREN", end = " ")
        elif self.tokenType == TokenType.RIGHT_PAREN:
            print("RIGHT_PAREN", end = " ")
        elif self.tokenType == TokenType.COMMA:
            print("      COMMA", end = " ")
        elif self.tokenType == TokenType.LINE_END:
            print("   LINE_END", end = " ")

        print(f"{self.lexeme} ")


class TokenList:
    def __init__(self):
        self.tokens: "list[Token]" = []
        self.current = 0

    def add(self, tokenType: int, lexeme: str, line: int) -> None:
        self.tokens.append(Token(tokenType, lexeme, line))

    def advance(self) -> Token:
        self.current += 1
        
        if self.current - 1 >= len(self.tokens):
            return None

        return self.tokens[self.current - 1]

    def peek(self) -> Token:
        return self.tokens[self.current]

    def is_at_end(self) -> bool:
        return self.current >= len(self.tokens)

    def skip_line(self) -> None:
        cur = self.advance()
        while cur != None and cur.tokenType != TokenType.LINE_END:
            cur = self.advance()


class CompileInfo:
    def __init__(self):
        self.projectName = ""
        self.compiler = "gcc"
        self.languageVersion = "c99"
        self.arch = "64"
        self.outputType = "executable"
        self.buildType = "release"
        self.files: "list[str]" = []
        self.sourcePaths: "list[str]" = []
        self.constants: "list[str]" = []
        self.includePaths: "list[str]" = []
        self.libraries: "list[str]" = []
        self.objectFiles: "list[str]" = []
        self.compilerFlags: "list[str]" = []
        self.linkerFlags: "list[str]" = []


hadError = False

def main() -> None:
    buildFile = None
    for arg in sys.argv[1:]:
        if arg in {"-h", "--help"}:
            print_help()
            exit(0)
        else:
            buildFile = arg

    if buildFile == None:
        print_error("Requires build file. Use -h for more info.")
        exit(1)

    tokenList = None
    try:
        tokenList = scan_file(buildFile)
    except OSError:
        print_error(f"File \"{buildFile}\" not found.")
        exit(2)

    #for token in tokenList.tokens:
    #    token.print()

    compileInfo = parse_tokens(tokenList)

    global hadError
    if hadError:
        exit(1)

    command = build_compile_command(compileInfo)
    print(command)

    start = time.time_ns()
    result = os.system(command)
    end = time.time_ns()
    elapsed = (end - start) / (10 ** 9)
    if result == 0:
        print("Compiled successfuly in {0} seconds".format(round(elapsed, 2)))


def build_compile_command(compileInfo: CompileInfo) -> str:
    if compileInfo.compiler == "gcc":
        return build_gcc_command(compileInfo)
    elif compileInfo.compiler == "clang":
        return build_clang_command(compileInfo)
    elif compileInfo.compiler == "clang-cl":
        return build_clang_cl_command(compileInfo)
    elif compileInfo.compiler == "cl":
        return build_cl_command(compileInfo)


def build_gcc_command(compileInfo: CompileInfo) -> str:
    command = "gcc -Wall -std=" + compileInfo.languageVersion
    
    if compileInfo.buildType == "release":
        command = command + " -O2"
    else:
        command = command + " -O0 -g"

    command = command + " -m" + compileInfo.arch
    command = command + " " + str.join(" ", compileInfo.compilerFlags)
    command = command + " -D" + str.join(" -D", compileInfo.constants)
    command = command + " -I" + str.join(" -I", compileInfo.includePaths)
    command = command + " " + str.join(" ", compileInfo.files)
    command = command + " " + str.join(" ", compileInfo.sourcePaths)

    if compileInfo.outputType == "executable":
        command = command + " -o " + compileInfo.projectName + get_executable_file_extension()
        command = command + " " + str.join(" ", compileInfo.linkerFlags)
        command = command + " " + get_gcc_libraries(compileInfo.libraries)
    
    elif compileInfo.outputType == "shared":
        command = command + "-shared -o " + compileInfo.projectName + get_executable_file_extension()
        command = command + " " + str.join(" ", compileInfo.linkerFlags)
        command = command + " " + get_gcc_libraries(compileInfo.libraries)

    elif compileInfo.outputType == "object":
        command = command + " -c"

    return command


def build_clang_command(compileInfo: CompileInfo) -> str:
    command = "clang -mno-incremental-linker-compatible -Wall -std=" + compileInfo.languageVersion

    if compileInfo.buildType == "release":
        command = command + " -O2"
    else:
        command = command + " -O0 -g"

    command = command + " -m" + compileInfo.arch
    command = command + " " + str.join(" ", compileInfo.compilerFlags)
    command = command + " -D" + str.join(" -D", compileInfo.constants)
    command = command + " -I" + str.join(" -I", compileInfo.includePaths)
    command = command + " " + str.join(" ", compileInfo.files)
    command = command + " " + str.join(" ", compileInfo.sourcePaths)

    if compileInfo.outputType == "executable":
        command = command + " -o " + compileInfo.projectName + get_executable_file_extension()
        command = command + " " + str.join(" ", compileInfo.linkerFlags)
        command = command + " " + get_gcc_libraries(compileInfo.libraries)
    
    elif compileInfo.outputType == "shared":
        command = command + "-shared -o " + compileInfo.projectName + get_executable_file_extension()
        command = command + " " + str.join(" ", compileInfo.linkerFlags)
        command = command + " " + get_gcc_libraries(compileInfo.libraries)

    elif compileInfo.outputType == "object":
        command = command + " -c"

    return command

    
def get_gcc_libraries(libraries: "list[str]") -> str:
    result = ""
    for lib in libraries:
        if lib.endswith(get_object_file_extension()):
            result = result + " " + lib
        else:
            result = result + " -l" + lib
    return result


def build_clang_cl_command(compileInfo: CompileInfo) -> str:
    command = "clang-cl /FC /W4 -Xclang -std=" + compileInfo.languageVersion + " -m" + compileInfo.arch

    if compileInfo.buildType == "release":
        command = command + " /O2 /Oi /fp:fast"
    else:
        command = command + " /Od /Zi"

    command = command + " " + str.join(" ", compileInfo.compilerFlags)
    command = command + " -D" + str.join(" -D", compileInfo.constants)
    command = command + " -I" + str.join(" -I", compileInfo.includePaths)
    command = command + " " + str.join(" ", compileInfo.files)
    command = command + " " + str.join(" ", compileInfo.sourcePaths)

    if compileInfo.outputType == "executable":
        command = command + " /o " + compileInfo.projectName + get_executable_file_extension()
        command = command + " /link /INCREMENTAL:NO /OPT:REF " + str.join(" ", compileInfo.linkerFlags)
        command = command + " " + get_cl_libraries(compileInfo.libraries)
    
    elif compileInfo.outputType == "shared":
        command = command + " /o " + compileInfo.projectName + get_executable_file_extension()
        command = command + " /link /INCREMENTAL:NO /OPT:REF " + str.join(" ", compileInfo.linkerFlags)
        command = command + " " + get_cl_libraries(compileInfo.libraries) + " /DLL"

    elif compileInfo.outputType == "object":
        command = command + " /c /Fo\"" + compileInfo.outputType + "\"\\"

    return command


def build_cl_command(compileInfo: CompileInfo) -> str:    
    command = "cl /FC /W4 /std:" + compileInfo.languageVersion

    if compileInfo.buildType == "release":
        command = command + " /O2 /Oi /fp:fast"
    else:
        command = command + " /Od /Zi"

    command = command + " " + str.join(" ", compileInfo.compilerFlags)
    command = command + " -D" + str.join(" -D", compileInfo.constants)
    command = command + " -I" + str.join(" -I", compileInfo.includePaths)
    command = command + " " + str.join(" ", compileInfo.files)
    command = command + " " + str.join(" ", compileInfo.sourcePaths)

    if compileInfo.outputType == "executable":
        command = command + " /link /INCREMENTAL:NO /OPT:REF " + str.join(" ", compileInfo.linkerFlags)
        command = command + " " + get_cl_libraries(compileInfo.libraries)
        command = command + " /OUT:" + compileInfo.projectName + get_executable_file_extension()
    
    elif compileInfo.outputType == "shared":
        command = command + " /link /INCREMENTAL:NO /OPT:REF " + str.join(" ", compileInfo.linkerFlags)
        command = command + " " + get_cl_libraries(compileInfo.libraries) + " /DLL"
        command = command + " /OUT:" + compileInfo.projectName + get_executable_file_extension()

    elif compileInfo.outputType == "object":
        command = command + " /c /Fo\"" + compileInfo.outputType + "\"\\"

    return command


def get_cl_libraries(libraries: str) -> str:
    result = ""
    for lib in libraries:
        result = result + " " + lib + get_static_library_file_extension()
    return result


def get_executable_file_extension() -> str:
    osName = platform.system()
    if osName == "Windows":
        return ".exe"
    else:
        return ""


def get_shared_library_file_extension() -> str:
    osName = platform.system()
    if osName == "Windows":
        return ".dll"
    else:
        return ".so"


def get_object_file_extension() -> str:
    osName = platform.system()
    if osName == "Window":
        return ".obj"
    else:
        return ".o"


def get_static_library_file_extension() -> str:
    osName = platform.system()
    if osName == "Window":
        return ".lib"
    else:
        return ".a"


def print_error(*args, **kwdargs) -> None:
    global hadError
    hadError = True
    print(*args, file = sys.stderr, **kwdargs)


def print_help() -> None:
    help = """\
Usage: oatbuild -h --help \"buildfile\"

Command list:
        SetProjectName(x) -> projectName
        SetCompiler(x) -> gcc/cl/clang/clang-cl
        SetLanguageVersion(x) -> c89/c99/c11/c17
        SetTargetArch(x) -> 32/64
        SetOutputType(x) -> shared/object/executable
        SetBuildType(x) -> debug/release
        AddFile(...) -> filename1, filename2
        AddSourcePath(...) -> directory1, directory2
        AddConstant(...) -> constant1=1, constant2=2
        AddIncludePath(...) -> path1, path2
        AddLibrary(...) -> library1, library2
        AddObjectFile(...) -> object1, object2
        AddCompilerFlag(...) -> flag1, flag2
        AddLinkerFlag(...) -> flag1, flag2"""
    print(help)


def is_valid_character(c: str) -> bool:
    return c.isalnum() or c in {"_", "-", ".", "/", "\\", ":", "="}


def scan_file(fileName: str) -> TokenList:
    tokenList = TokenList()

    with open(fileName) as file:
        for index, line in enumerate(file):
            #empty new lines skipped
            if line[0] == "\n":
                continue

            tokenStart = 0
            tokenEnd = 0

            while tokenStart < len(line):
                c = line[tokenStart]
                if c == "(":
                    tokenList.add(TokenType.LEFT_PAREN, "(", index + 1)
                elif c == ")":
                    tokenList.add(TokenType.RIGHT_PAREN, ")", index + 1)
                elif c == ",":
                    tokenList.add(TokenType.COMMA, ",", index + 1)
                elif c == "\n":
                    tokenList.add(TokenType.LINE_END, "\\n", index + 1)
                elif c in {" ", "\t", "\0"}:
                    pass
                else:
                    while tokenEnd < len(line) and is_valid_character(line[tokenEnd]):
                        tokenEnd += 1
                    tokenList.add(TokenType.STRING, line[tokenStart:tokenEnd], index + 1)

                tokenStart = tokenEnd
                tokenEnd += 1

    return tokenList

def parse_tokens(tokenList: TokenList) -> CompileInfo:
    compileInfo = CompileInfo()
    
    while(not tokenList.is_at_end()):
        token = tokenList.peek()
        
        if token.tokenType == TokenType.STRING:
            handle_command(tokenList, compileInfo)
        else:
            print_error(f"[{token.line}] at -> \"{token.lexeme}\" Commands must begin with a string.")
            tokenList.skip_line()

    return compileInfo


def handle_command(tokenList: TokenList, compileInfo: CompileInfo) -> None:
    command = tokenList.advance()
    
    if command.lexeme == "SetProjectName":
        param = simple_command(tokenList, command)
        if param != None:
            compileInfo.projectName = param.lexeme

    elif command.lexeme == "SetCompiler":
        param = simple_command(tokenList, command)
        if param != None:
            compiler = param.lexeme
            if compiler in {"gcc", "cl", "clang", "clang-cl"}:
                compileInfo.compiler = compiler
            else:
                print_error(f"[{param.line}] at -> \"{param.lexeme}\" Invalid compiler.")

    elif command.lexeme == "SetLanguageVersion":
        param = simple_command(tokenList, command)
        if param != None:
            version = param.lexeme
            if version in {"c89", "c99", "c11", "c17"}:
                compileInfo.languageVersion = version
            else:
                print_error(f"[{param.line}] at -> \"{param.lexeme}\" Invalid language version.")

    elif command.lexeme == "SetTargetArch":
        param = simple_command(tokenList, command)
        if param != None:
            arch = param.lexeme
            if arch in {"32", "64"}:
                compileInfo.arch = arch
            else:
                print_error(f"[{param.line}] at -> \"{param.lexeme}\" Invalid architeture.")
        
    elif command.lexeme == "SetOutputType":
        param = simple_command(tokenList, command)
        if param != None:
            outputType = param.lexeme
            if outputType in {"shared", "object", "executable"}:
                compileInfo.outputType = outputType
            else:
                print_error(f"[{param.line}] at -> \"{param.lexeme}\" Invalid output type.")

    elif command.lexeme == "SetBuildType":
        param = simple_command(tokenList, command)
        if param != None:
            buildType = param.lexeme
            if buildType in {"debug", "release"}:
                compileInfo.buildType = buildType
            else:
                print_error(f"[{param.line}] at -> \"{param.lexeme}\" Invalid build type.")
        
    elif command.lexeme == "AddFile":
        params = complex_command(tokenList, command)
        if params != None:
            for param in params:
                compileInfo.files.append(param.lexeme)

    elif command.lexeme == "AddSourcePath":
        params = complex_command(tokenList, command)
        if params != None:
            for param in params:
                compileInfo.sourcePaths.append(param.lexeme)
        
    elif command.lexeme == "AddConstant":
        params = complex_command(tokenList, command)
        if params != None:
            for param in params:
                compileInfo.constants.append(param.lexeme)
        
    elif command.lexeme == "AddIncludePath":
        params = complex_command(tokenList, command)
        if params != None:
            for param in params:
                compileInfo.includePaths.append(param.lexeme)

    elif command.lexeme == "AddLibrary":
        params = complex_command(tokenList, command)
        if params != None:
            for param in params:
                compileInfo.libraries.append(param.lexeme)

    elif command.lexeme == "AddObjectFile":
        params = complex_command(tokenList, command)
        if params != None:
            for param in params:
                compileInfo.objectFiles.append(param.lexeme)
        
    elif command.lexeme == "AddCompilerFlag":
        params = complex_command(tokenList, command)
        if params != None:
            for param in params:
                compileInfo.compilerFlags.append(param.lexeme)

    elif command.lexeme == "AddLinkerFlag":
        params = complex_command(tokenList, command)
        if params != None:
            for param in params:
                compileInfo.linkerFlags.append(param.lexeme)

    else:
        print_error(f"[{command.line}] at -> \"{command.lexeme}\" Unkown command.")
        tokenList.skip_line(command)


def complex_command(tokenList: TokenList, command: Token) -> "list[Token]":
    params = get_complex_command_params(tokenList, command)
    if params == None and hadError == True:
        tokenList.skip_line()
    elif params == None:
        print_error(f"[{command.line}] at -> \"{command.lexeme}\" Expected parameters after command.")
        tokenList.skip_line()
    else:
        tokenList.skip_line()
        return params

    return None


def get_complex_command_params(tokenList: TokenList, command: Token) -> "list[Token]":
    lparen = tokenList.advance()
    if lparen == None or lparen.tokenType != TokenType.LEFT_PAREN:
        print_error(f"[{command.line}] at -> \"{command.lexeme}\" Expected \"(\" after command.")
        return None

    params = []
    consume_param(tokenList, params)
    if len(params) == 0:
        return None

    rparen = tokenList.advance()
    if rparen == None or rparen.tokenType != TokenType.RIGHT_PAREN:
        print_error(f"[{command.line}] at -> \"{command.lexeme}\" Expected \")\" after parameters.")
        return None

    return params


def consume_param(tokenList: TokenList, result: "list[Token]") -> None:
    param = tokenList.peek()
    if param == None:
        return

    if param.tokenType == TokenType.STRING:
        tokenList.advance()
        result.append(param)
        consume_comma(tokenList, result)


def consume_comma(tokenList: TokenList, result: "list[Token]") -> None:
    comma = tokenList.peek()
    if comma == None:
        return

    if comma.tokenType == TokenType.COMMA:
        tokenList.advance()
        consume_param(tokenList, result)


def simple_command(tokenList: TokenList, command: Token) -> Token:
    param = get_simple_command_param(tokenList, command)
    if param == None and hadError == True:
        tokenList.skip_line()
    elif param == None:
        print_error(f"[{command.line}] at -> \"{command.lexeme}\" Expected parameter after command.")
        tokenList.skip_line()
    else:
        tokenList.skip_line()
        return param

    return None


def get_simple_command_param(tokenList: TokenList, command: Token) -> Token:
    lparen = tokenList.advance()
    if lparen == None or lparen.tokenType != TokenType.LEFT_PAREN:
        print_error(f"[{command.line}] at -> \"{command.lexeme}\" Expected \"(\" after command.")
        return None

    param = tokenList.advance()
    if param == None:
        return None

    rparen = tokenList.advance()
    if rparen == None or rparen.tokenType != TokenType.RIGHT_PAREN:
        print_error(f"[{command.line}] at -> \"{command.lexeme}\" Expected \")\" after parameter.")
        return None

    return param


if __name__ == "__main__":
    main()