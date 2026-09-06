class CodeCleaner:
    """Utility for cleaning source code."""
    
    @staticmethod
    def remove_comments_python(code: str) -> str:
        """Remove Python comments."""
        lines = []
        in_multiline = False
        for line in code.split('\n'):
            if in_multiline:
                if '"""' in line or "'''" in line:
                    in_multiline = False
                continue
            if '"""' in line or "'''" in line:
                in_multiline = True
                continue
            if '#' in line:
                line = line[:line.index('#')]
            lines.append(line)
        return '\n'.join(lines)
    
    @staticmethod
    def remove_comments_js(code: str) -> str:
        """Remove JavaScript comments."""
        result = []
        i = 0
        while i < len(code):
            if code[i:i+2] == '//':
                end = code.find('\n', i)
                if end == -1:
                    break
                i = end + 1
            elif code[i:i+2] == '/*':
                end = code.find('*/', i)
                if end == -1:
                    break
                i = end + 2
            else:
                result.append(code[i])
                i += 1
        return ''.join(result)
    
    @staticmethod
    def remove_comments_cs(code: str) -> str:
        """Remove C# comments."""
        result = []
        i = 0
        while i < len(code):
            if code[i:i+2] == '//':
                end = code.find('\n', i)
                if end == -1:
                    break
                i = end + 1
            elif code[i:i+2] == '/*':
                end = code.find('*/', i)
                if end == -1:
                    break
                i = end + 2
            else:
                result.append(code[i])
                i += 1
        return ''.join(result)
    
    @staticmethod
    def remove_comments(code: str, language: str) -> str:
        """Remove comments based on language."""
        if language == 'python':
            return CodeCleaner.remove_comments_python(code)
        elif language == 'javascript':
            return CodeCleaner.remove_comments_js(code)
        elif language == 'csharp':
            return CodeCleaner.remove_comments_cs(code)
        return code