import re

def cpp_to_rust_class_converter(cpp_code):
    # Patterns for C++ constructs
    class_pattern = r'class\s+(\w+)\s*\{(.*?)\};'  # Match C++ classes

    def convert_class(match):
        cpp_class_name = match.group(1)
        class_body = match.group(2).strip()

        # Pass cpp_class_name to convert_class_body
        struct_fields, impl_methods = convert_class_body(cpp_class_name, class_body)

        # Create Rust struct and impl block
        rust_struct = f"pub struct {cpp_class_name} {{\n{struct_fields}\n}}\n\n"
        rust_impl = f"impl {cpp_class_name} {{\n{impl_methods}\n}}\n" if impl_methods else ""

        return rust_struct + rust_impl

    def convert_class_body(cpp_class_name, class_body):
        # Remove access specifiers like public, private, protected
        class_body = re.sub(r'(public|private|protected):', '', class_body)

        # Use a refined regex to capture only member variable declarations
        variable_pattern = r'\b(\w+)\s+(\w+)\b(?!\s*\() *;'
        function_pattern = r'(\w+)\s+(\w+)\(([^)]*)\)\s*\{(.*?)\}'  # unchanged
        constructor_pattern = rf'{cpp_class_name}\s*\(([^)]*)\)\s*\{{(.*?)\}}'

        struct_fields = []
        impl_methods = []
        member_variables = []

        # Extract member variables using the refined regex
        for var_match in re.finditer(variable_pattern, class_body):
            c_type = var_match.group(1)
            var_name = var_match.group(2)
            rust_type = cpp_type_to_rust(c_type)
            struct_fields.append(f"    pub {var_name}: {rust_type},")
            member_variables.append(var_name)

        # Process constructors (example remains unchanged)
        for ctor_match in re.finditer(constructor_pattern, class_body, re.DOTALL):
            params = ctor_match.group(1)
            body = ctor_match.group(2).strip()
            rust_params = convert_parameters(params)
            # ... code to extract field initializations ...
            impl_methods.append(
                f"    pub fn new({rust_params}) -> Self {{\n"
                f"        // Processed initialization\n"
                f"        Self {{\n"
                f"            // field initializations here\n"
                f"        }}\n"
                f"    }}"
            )
            break

        # Process methods (change &self to &mut self and use refined substitution)
        for func_match in re.finditer(function_pattern, class_body, re.DOTALL):
            return_type = cpp_type_to_rust(func_match.group(1))
            func_name = func_match.group(2)
            params = func_match.group(3)
            body = func_match.group(4).strip()

            # Skip constructors that match the class name
            if func_name == cpp_class_name:
                continue

            rust_params = convert_parameters(params)

            # Use negative lookbehind to prevent adding multiple `self.`
            for var in member_variables:
                body = re.sub(rf'(?<!self\.)\b{var}\b', f'self.{var}', body)

            # Change &self to &mut self because these methods modify state
            impl_methods.append(
                f"    pub fn {func_name}(&mut self, {rust_params}) -> {return_type} {{\n"
                f"        {body}\n"
                f"    }}"
            )

        return "\n".join(struct_fields), "\n\n".join(impl_methods)


    def convert_parameters(params):
        """Converts C++ parameters to Rust parameters."""
        if not params.strip():
            return ""
        param_list = []
        for param in params.split(','):
            param = param.strip()
            if " " in param:
                c_type, name = param.rsplit(" ", 1)
                rust_type = cpp_type_to_rust(c_type)
                param_list.append(f"{name}: {rust_type}")
        return ", ".join(param_list)

    def cpp_type_to_rust(cpp_type):
        """Converts a C++ type to its Rust equivalent."""
        type_mapping = {
            "int": "i32",
            "float": "f32",
            "double": "f64",
            "char": "char",
            "bool": "bool",
            "std::string": "String",
            "void": "()",
        }
        return type_mapping.get(cpp_type, cpp_type)  # Default to the same type if not found

    # Apply the class conversion pattern
    rust_code = re.sub(class_pattern, convert_class, cpp_code, flags=re.DOTALL)  # Use DOTALL to match multiline class body
    return rust_code

def preprocess(input_file, output_file):
    CPP_KEYWORDS = [
        "alignas", "alignof", "asm", "auto", "bitand", "bitor", "bool", "break",
        "case", "catch", "char", "char8_t", "char16_t", "char32_t", "class",
        "const", "constexpr", "const_cast", "continue", "co_await", "co_return",
        "co_yield", "decltype", "default", "delete", "do", "double", "dynamic_cast",
        "else", "enum", "explicit", "export", "extern", "false", "float", "for",
        "friend", "goto", "if", "import", "inline", "int", "long", "mutable",
        "namespace", "new", "nullptr", "operator", "or", "or_eq", "private",
        "protected", "public", "reinterpret_cast", "requires", "return", "short",
        "signed", "sizeof", "static", "static_assert", "static_cast", "struct",
        "switch", "template", "this", "throw", "true", "try", "typedef", "typeid",
        "typename", "union", "unsigned", "using", "virtual", "void", "volatile",
        "wchar_t", "while", "xor", "xor_eq"
    ]

    # Precompile regex patterns
    OPERATOR_REGEX = re.compile(r'\s*([=><+\-*/%{};(),]+)\s*')
    INCLUDE_REGEX = re.compile(r'#include\s*<\s*([^\s>]+)\s*>')
    KEYWORD_REGEX = re.compile(r'\b(' + '|'.join(CPP_KEYWORDS) + r')\b\s*([a-zA-Z_][a-zA-Z0-9_]*)')
    MULTIPLE_SPACES_REGEX = re.compile(r'\s{2,}')
    COUT_CIN_REGEX = re.compile(r'\s*(<<|>>)\s*')

    def process_code_line(line):
        # Skip lines containing 'return 0;'
        if 'return 0;' in line:
            return None
        if line.startswith("#include") or line.startswith("using namespace"):
            return None
        if re.match(r'^\s*for\s*\(.*\)', line):  # Check for a for loop
            if re.search(r'\b\+\+(\w+)\b', line):  # Check for ++i
                print("Converting ++i to i++ in for loop")
                line = re.sub(r'\b\+\+(\w+)\b', r'\1++', line)

        
        line = re.sub(r'\b\+\+(\w+)\b', r'\1 += 1', line)  # Matches ++i
        line = re.sub(r'\b(\w+)\+\+\b', r'\1 += 1', line)  # Matches i++

        # Replace --i and i-- with i -= 1
        line = re.sub(r'\b\-\-(\w+)\b', r'\1 -= 1', line)  # Matches --i
        line = re.sub(r'\b(\w+)\-\-\b', r'\1 -= 1', line)  # Matches i--
        # Remove unwanted spaces and format the code
        line = OPERATOR_REGEX.sub(r'\1', line)
        line = INCLUDE_REGEX.sub(r'#include<\1>', line)
        line = KEYWORD_REGEX.sub(r'\1 \2', line)
        line = MULTIPLE_SPACES_REGEX.sub(' ', line)
        line = COUT_CIN_REGEX.sub(r'\1', line)
        
        return line.strip()

    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()

        formatted_lines = []
        inside_switch = False
        brace_stack = []  # Track opening and closing braces

        for i, line in enumerate(lines):
            stripped = line.strip()
            # Replace both 'string' and 'std::string' with 'String'
            stripped = re.sub(r'\bstring\b', 'String', stripped)

            if stripped.startswith("switch"):
                inside_switch = True
                formatted_lines.append(stripped)
                continue

            # Handle the default case
            if inside_switch and stripped.startswith("default:"):
                formatted_lines.append(f"        {stripped}")  # Properly indent default
                continue

            if inside_switch:
                # Push opening braces to the stack
                if "{" in stripped:
                    brace_stack.append("{")
                    #print("Open : ",stripped)
                # Handle closing braces
                if "}" in stripped:
                    #print("Close :",stripped)
                    if brace_stack:
                        brace_stack.pop()  # Pop matching opening brace
                    else:
                        # Add #EOD before the unmatched closing brace
                        formatted_lines.append("        #EOD")  # Properly indent the #EOD
                        inside_switch = False  # Exit switch context
                    formatted_lines.append(stripped)  # Add the closing brace
                    continue
            if "{" in stripped and "}" in stripped and stripped.index("{") < stripped.index("}"):
                # Skip processing if this is part of a control structure (e.g., if, else, while)
                control_keywords = ["if", "else", "while", "for", "switch"]
                if any(stripped.startswith(keyword) for keyword in control_keywords):
                    # Let it be handled normally
                    pass
                else:
                    # Split the line into the content before '{', inside braces, and after '}'
                    before_brace = stripped[:stripped.index("{")].strip()
                    inside_brace = stripped[stripped.index("{") + 1:stripped.index("}")].strip()
                    
                    formatted_lines.append(f"{before_brace} {{")  # Add the opening brace on a new line
                    if inside_brace:  # Add the content between '{' and '}'
                        formatted_lines.append(f"    {inside_brace}")
                    formatted_lines.append("}")  # Add the closing brace on a new line
                    continue  # ✅ Don't process the original line again
            elif stripped.endswith("}"):
                # Ensure closing brace '}' is on a separate line
                content_before_brace = stripped[:-1].strip()
                if content_before_brace:  # Add content before '}' if it exists
                    formatted_lines.append(content_before_brace)
                formatted_lines.append("}") 
                continue # Add closing brace on its own line



            # Process code line through formatting functions
            processed_line = process_code_line(line)
            if processed_line is not None:
                formatted_lines.append(processed_line)

        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.write("\n".join(formatted_lines))

    except FileNotFoundError:
        print(f"Error: The file {input_file} was not found.")
    except IOError as e:
        print(f"File error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def convert(input_file, output_file):
    # Dictionary mapping C++ types to Rust types
    variable_types = {}
    rust_type = {
        "int": "i32",
        "unsigned int": "u32",
        "char8_t": "u8",
        "char16_t": "u16",
        "char32_t": "u32",
        "wchar_t": "char",
        "long": "i64",
        "unsigned long": "u64",
        "usize":"usize",
        "short": "i16",
        "unsigned short": "u16",
        "char": "char",
        "unsigned char": "u8",
        "bool": "bool",
        "float": "f32",
        "double": "f64",
        "long double": "f64",
        "void": "()",
        "string": "String",
        "std::string": "String",
        "std::vector": "Vec",
        "std::map": "HashMap",
        "std::set": "HashSet",
        "std::pair": "(T1, T2)",
        "size_t": "usize",
        "ptrdiff_t": "isize"
    }

    with open(input_file, "r") as cpp_file:
        cpp_code1 = cpp_file.read()
    cpp_code = cpp_to_rust_class_converter(cpp_code1)

    with open(input_file, "w") as cpp_file:
        cpp_file.write(cpp_code)

    with open(input_file, "r") as cpp_file:
        cpp_code = cpp_file.readlines()
    rust_code = []

    mutable_variables = set()

    # First pass to identify mutable variables
    for line in cpp_code:
        stripped = line.strip()

        # Identify variable assignments or updates
        match = re.match(r"^(\w+)\s*=.*", stripped)
        if match:
            mutable_variables.add(match.group(1))

        # Check for increment/decrement operations
        if "++" in stripped or "--" in stripped or "+=" in stripped or "-=" in stripped:
            var_match = re.match(r"^(\w+).*", stripped)
            if var_match:
                mutable_variables.add(var_match.group(1))
        inside_class =  False


    # Second pass to generate Rust code
    for i, line in enumerate(cpp_code):
        stripped = line.strip()
        object_instantiation_match = re.match(r'^\s*(\w+)\s+(\w+)\s*;$', stripped)
        if object_instantiation_match:
            class_name, var_name = object_instantiation_match.groups()
            rust_code.append(f"let mut {var_name} = {class_name}{{}};")
            continue
        if re.match(r'^\s*(\w+)\s+(\w+)\((.*?)\);', stripped):
            try:
                # Match object declaration
                object_match = re.match(r'^\s*(\w+)\s+(\w+)\((.*?)\);', stripped)
                if object_match:
                    class_name, object_name, constructor_args = object_match.groups()
                    rust_code.append(f"let {object_name} = {class_name}::new({constructor_args});")
            except Exception as e:
                rust_code.append(f"// Error converting object declaration: {e}")
                rust_code.append("// Original line: " + line)

        def handle_inline_block(keyword, line):
            try:
                condition = re.search(rf'{keyword}\s*\((.*?)\)', line).group(1) if '(' in line else None
                body_match = re.search(r'\{(.*)\}', line)
                body = body_match.group(1) if body_match else None

                if condition:
                    rust_code.append(f"{keyword} {condition} {{")
                else:
                    rust_code.append(f"{keyword} {{")

                if body:
                    body_parts = body.split(";")
                    for part in body_parts:
                        part = part.strip()
                        if part:
                            rust_code.append(f"    {part};")

                rust_code.append("}")
            except Exception as e:
                rust_code.append(f"// Error processing inline {keyword} statement: {e}")
                rust_code.append("// Original line: " + line)

        single_for_success = False  # Flag to check if single-variable for loop succeeds

        if re.search(r'\bTrue\b', stripped):
            stripped = re.sub(r'\bTrue\b', 'true', stripped)


        elif any(kw in stripped for kw in ["typedef", "enum", "pub struct", "cout", "cin", "nullptr", "new int(", "delete", "sizeof("]):
            # Typedef
            typedef_match = re.match(r'^\s*typedef\s+(\w+)\s+(\w+);', stripped)
            if typedef_match:
                c_type, alias = typedef_match.groups()
                rust_equiv = rust_type.get(c_type, c_type)
                rust_code.append(f"type {alias} = {rust_equiv};")
                continue

            # Enum start
            enum_start = re.match(r'^\s*enum\s+(\w+)\s*\{', stripped)
            if enum_start:
                rust_code.append(f"enum {enum_start.group(1)} {{")
                continue

            # Enum value line
            if stripped.endswith(",") and not stripped.startswith("pub"):
                rust_code.append(f"    {stripped.rstrip(',')},")
                continue

            # Enum end
            if stripped == "};":
                rust_code.append("}")
                continue

            # cout statements
            if "cout<<" in stripped:
                try:
                    parts = stripped.split("<<")
                    text = []
                    vars = []
                    for part in parts[1:]:
                        part = part.replace(";", "").strip()
                        if "endl" in part:
                            continue
                        if part.startswith('"') and part.endswith('"'):
                            text.append(part.strip('"'))
                        else:
                            text.append("{}")
                            vars.append(part)
                    if vars:
                        rust_code.append(f'println!("{ "".join(text) }", {", ".join(vars)});')
                    else:
                        rust_code.append(f'println!("{ "".join(text) }");')
                except:
                    rust_code.append(f"// Error in cout conversion: {stripped}")
                continue

            # cin statements
            if "cin>>" in stripped:
                try:
                    vars = stripped.replace("cin>>", "").split(">>")
                    for var in vars:
                        var = var.strip(" ;")
                        rust_code.append(f"let mut {var} = String::new();")
                        rust_code.append(f"std::io::stdin().read_line(&mut {var}).unwrap();")
                        rust_code.append(f"let {var}: i32 = {var}.trim().parse().unwrap();")
                except:
                    rust_code.append(f"// Error in cin conversion: {stripped}")
                continue

            # nullptr replacement
            if "nullptr" in stripped:
                rust_code.append(stripped.replace("nullptr", "None"))
                continue

            # new int(x)
            new_ptr_match = re.search(r'new int\((\d+)\)', stripped)
            if new_ptr_match:
                rust_code.append(f"let ptr = Box::new({new_ptr_match.group(1)});")
                continue

            # delete ptr;
            if "delete" in stripped:
                rust_code.append("// Rust handles memory deallocation automatically.")
                continue

            # sizeof()
            sizeof_match = re.search(r'sizeof\((\w+)\)', stripped)
            if sizeof_match:
                rust_code.append(f'std::mem::size_of::<{sizeof_match.group(1)}>();')
                continue

        # Try handling the single-variable for loop
        elif stripped.startswith("for"):
            try:  
                header = stripped[4:].strip("()").strip("{").strip()
                init, cond, incr = [x.strip() for x in header.split(';')]

                if "int" in init:
                    init = init.replace("int", "").strip()
                var, start = init.split("=")
                var = var.strip()
                start = start.strip()

                end_operator = "<" if "<" in cond else ">"
                end = cond.split(end_operator)[1].strip()

                if "++" in incr:
                    step = 1
                elif "--" in incr:
                    step = -1
                elif "+=" in incr:
                    step = int(incr.split("+=")[1].strip(")").strip("{"))
                elif "-=" in incr:
                    step = -int(incr.split("-=")[1].strip(")").strip("{"))
                else:
                    rust_code.append("// Unsupported increment in for loop: " + line)
                    continue

                if step > 0:
                    rust_code.append(f"for {var} in ({start}..{end}).step_by({step}) {{")
                else:
                    rust_code.append(f"for {var} in ({start}..{end}).rev().step_by({abs(step)}) {{")
                    
                single_for_success = True  # Set to True since single-variable for loop succeeded
                continue

            except Exception as e:
                rust_code.append(f"// Error converting single-variable for loop: {e}")
                rust_code.append("// Trying to process multi-variable for loop...")

        # If single-variable for loop failed, try the multi-variable for loop
        if not single_for_success and stripped.startswith("for"):
            try:
                # Try handling multi-variable for loop
                match = re.match(r"for\s*\(([^;]+);([^;]+);([^;]+)\)", stripped)
                if match:
                    init, cond, incr = match.groups()

                    # Parse the initialization part (e.g., "int i=0, j=10")
                    init_vars = re.findall(r"(\w+)\s*=\s*([^,]+)", init)
                    rust_init = [f"let mut {var.strip()} = {val.strip()};" for var, val in init_vars]

                    # Parse the condition part (e.g., "i<5 && j>0")
                    conditions = cond.strip()

                    # Parse the increment part (e.g., "i++, j--")
                    increments = re.findall(r"(\w+)(\+\+|--|[\+\-]=\s*\d+)", incr)
                    rust_increments = []
                    for var, op in increments:
                        var = var.strip()
                        if op == "++":
                            rust_increments.append(f"{var} += 1;")
                        elif op == "--":
                            rust_increments.append(f"{var} -= 1;")
                        elif "+=" in op or "-=" in op:
                            rust_increments.append(f"{var} {op};")
                        else:
                            rust_code.append(f"// Unsupported increment: {op}")

                    # Add initialization to Rust code
                    rust_code.extend(rust_init)

                    # Add the while loop header
                    rust_code.append(f"while {conditions} {{")

                    # Add increments to the end of the loop body
                    for inc in rust_increments:
                        rust_code.append(f"    {inc}")
                else:
                    rust_code.append("// Unsupported for loop structure: ")
                continue
            except Exception as e:
                rust_code.append(f"// Error converting multi-variable for loop: {e}")
                rust_code.append("// Original line: ")
        elif stripped.startswith("int main"):
            rust_code.append(line.replace("int", "fn"))
        elif stripped.startswith("while"):
            condition = re.search(r'while\s*\((.*?)\)', stripped)
            if condition:
                rust_code.append(f"while {condition.group(1)} {{")
        elif stripped.startswith("if") and "{" in stripped and "}" in stripped:
            print("if")
            handle_inline_block("if", stripped)
        elif stripped.startswith("else if") and "{" in stripped and "}" in stripped:
            handle_inline_block("else if", stripped)
        elif stripped.startswith("else") and "{" in stripped and "}" in stripped:
            handle_inline_block("else", stripped)
        elif stripped.startswith("if"):
            condition = re.search(r'if\s*\((.*?)\)', stripped)
            if condition:
                rust_code.append(f"if {condition.group(1)} {{")
        elif stripped.startswith("else if"):
            condition = re.search(r'else if\s*\((.*?)\)', stripped)
            if condition:
                rust_code.append(f"else if {condition.group(1)} {{")
        elif stripped.startswith("else if"):
            condition = re.search(r'else if\s*\((.*?)\)', stripped)
            if condition:
                rust_code.append(f"else if {condition.group(1)} {{")
        elif stripped.startswith("}else if"):
            condition = re.search(r'}else if\s*\((.*?)\)', stripped)
            if condition:
                rust_code.append(f"}}else if {condition.group(1)} {{")
        elif stripped.startswith("else"):
            rust_code.append("else {")
        elif "cout" in stripped:
            try:
                parts = stripped.split("<<")
                formatted_text = []
                variables = []

                for part in parts[1:]:
                    part = part.replace(";", "").strip()
                    if "endl" in part:
                        continue

                    if part.startswith('"') and part.endswith('"'):
                        formatted_text.append(part.strip('"'))
                    else:
                        formatted_text.append("{}")
                        variables.append(part)

                rust_text = "".join(formatted_text)

                if variables:
                    rust_line = f'println!("{rust_text}", {", ".join(variables)});'
                else:
                    rust_line = f'println!("{rust_text}");'

                rust_code.append(rust_line)
            except Exception as e:
                rust_code.append(f"// Error converting cout: {e}")
                rust_code.append("// Original line: " + line)
        elif re.match(r'^\s*pub\s+fn\s+(\w+)\s*\(([^)]*)\)\s*(->\s*[\w:<>]+)?\s*{', stripped):
            # Skip processing if this is a `new` function
            if "pub fn new" in stripped:
                rust_code.append(stripped)
                continue
            # Otherwise, handle other functions
            try:
                func_match = re.match(r'^\s*pub\s+fn\s+(\w+)\s*\(([^)]*)\)\s*(->\s*[\w:<>]+)?\s*{', stripped)
                func_name, params, return_type = func_match.groups()
                rust_code.append(f"fn {func_name}({params}) {return_type or ''} {{")
            except Exception as e:
                rust_code.append(f"// Error converting function: {e}")


        # Dictionary to store variable names and their types
        elif re.match(r'^\s*(?:inline\s+)?(?:static\s+)?(?:virtual\s+)?(?:explicit\s+)?([\w:<>]+)\s+(\w+)\s*\(\s*([^)]*)?\s*\)\s*(?:const)?\s*;', stripped):
            continue

        elif re.match(r'^\s*(?:inline\s+)?(?:static\s+)?(?:virtual\s+)?(?:explicit\s+)?([\w<>]+)\s+(\w+)\s*\(([^)]*)\)\s*(?:const)?\s*(\{)?', stripped):
            try:
                # Match function signature components
                func_match = re.match(
                    r'^\s*(?:inline\s+)?(?:static\s+)?(?:virtual\s+)?(?:explicit\s+)?([\w<>]+)\s+(\w+)\s*\(([^)]*)\)\s*(?:const)?\s*(\{)?', 
                    stripped
                )
                if func_match:
                    return_type, func_name, params, has_body = func_match.groups()

                    # Map return type to Rust
                    rust_return_type = rust_type.get(return_type, "/* UNKNOWN TYPE */")

                    # Process parameters
                    rust_params = []
                    if params.strip():
                        for param in params.split(","):
                            param_type, param_name = param.strip().rsplit(" ", 1)
                            rust_param_type = rust_type.get(param_type.strip(), "/* UNKNOWN TYPE */")
                            rust_params.append(f"{param_name}: {rust_param_type}")

                    # Construct Rust function signature
                    rust_func = f"fn {func_name}({', '.join(rust_params)})"
                    if rust_return_type != "()":  # Rust uses `()` for void
                        rust_func += f" -> {rust_return_type}"

                    rust_code.append(rust_func + " {" if has_body else rust_func)
            except Exception as e:
                rust_code.append(f"// Error converting function: {e}")
                rust_code.append("// Original line: " + line)

        elif re.match(r"^(int|unsigned int|long|unsigned long|short|unsigned short|char|unsigned char|bool|float|double|long double|size_t|ptrdiff_t|string)\s+.*;", stripped):
            try:
                # Match type and variable declarations
                match = re.match(r"^(int|unsigned int|long|unsigned long|short|unsigned short|char|unsigned char|bool|float|double|long double|size_t|ptrdiff_t|string)\s+(.+);$", stripped)

                if match:
                    ctype, vars_part = match.groups()
                    rust_type_mapped = rust_type.get(ctype, "UNKNOWN")
                    
                    if rust_type_mapped == "UNKNOWN":
                        rust_code.append(f"// Could not convert unknown C++ type: {ctype}")
                    else:
                        # Split variable declarations by commas and process each
                        variables = vars_part.split(",")
                        for var in variables:
                            var = var.strip()
                            if "=" in var:  # Variable with initialization
                                var_name, value = [v.strip() for v in var.split("=", 1)]
                                mut_prefix = "mut " if var_name in mutable_variables else ""
                                if rust_type_mapped == "String":
                                    rust_code.append(f"let {mut_prefix}{var_name} = String::from({value});")
                                else:
                                    rust_code.append(f"let {mut_prefix}{var_name}: {rust_type_mapped} = {value};")
                                variable_types[var_name] = rust_type_mapped  # Add to dictionary
                            else:  # Variable without initialization
                                mut_prefix = "mut " if var in mutable_variables else ""
                                rust_code.append(f"let {mut_prefix}{var}: {rust_type_mapped};")
                                variable_types[var] = rust_type_mapped  # Add to dictionary
                else:
                    rust_code.append(f"// Could not parse type declaration: {stripped}")
            except Exception as e:
                rust_code.append(f"// Error converting type declaration: {e}")
                rust_code.append("// Original line: " + line)

        elif stripped.startswith("switch"):
            try:
                condition = re.search(r'switch\s*\((.*?)\)', stripped).group(1)
                rust_code.append(f"match {condition} {{")
            except Exception as e:
                rust_code.append(f"// Error converting switch: {e}")
                rust_code.append("// Original line: " + line)
        elif stripped.startswith("case"):
            try:
                value = re.search(r'case\s+(.*?):', stripped).group(1)
                rust_code.append(f"    {value} => {{")
            except Exception as e:
                rust_code.append(f"// Error converting case: {e}")
                rust_code.append("// Original line: " + line)
        elif stripped.startswith("default:"):
            rust_code.append("    _ => {")
        elif stripped.startswith("using"):
            rust_code.append("type")
        elif stripped == "break;":
            rust_code.append("    },")
        elif stripped == "}":
            rust_code.append("}")
        elif stripped == "#EOD":
            rust_code.append("}")
        elif "cin>>" in stripped:
            try:
                variables = stripped.replace("cin>>", "").split(">>")
                for var in variables:
                    var = var.strip(";").strip()
                    rust_code.append(f"    let mut {var} = String::new();")
                    rust_code.append(f"    std::io::stdin().read_line(&mut {var}).unwrap();")
                    rust_code.append(f"    let {var}: {variable_types[var]} = {var}.trim().parse().unwrap();")
            except Exception as e:
                rust_code.append(f"// Error converting cin: {e}")
                rust_code.append("// Original line: " + line)
        elif " and " in stripped:
            rust_code.append(stripped.replace(" and ", " && "))

        elif " and_eq " in stripped:
            rust_code.append(stripped.replace(" and_eq ", " &= "))

        elif " xor_eq " in stripped:
            rust_code.append(stripped.replace(" xor_eq ", " ^= "))

        elif " xor " in stripped:
            rust_code.append(stripped.replace(" xor ", " ^ "))

        elif " or_eq " in stripped:
            rust_code.append(stripped.replace(" xor_eq ", " |= "))

        elif " or " in stripped:
            rust_code.append(stripped.replace(" xor ", " || "))

        elif " bitor " in stripped:
            rust_code.append(stripped.replace(" bitor ", " | "))

        elif " bitand " in stripped:
            rust_code.append(stripped.replace(" bitand ", " & "))

        elif " not_eq " in stripped:
            rust_code.append(stripped.replace(" xor_eq ", " != "))

        elif " not " in stripped:
            rust_code.append(stripped.replace(" xor ", " ! "))

        elif stripped.startswith("auto "):
            rust_code.append(f"let {stripped[5:]};")
        
        elif stripped.startswith("co_return"):
            rust_code.append("return")

        elif stripped == "break;":
            rust_code.append("break;")

        elif stripped == "continue;":
            rust_code.append("continue;")
        elif "throw" in stripped:
            rust_code.append("panic!")

        elif "void " in stripped:
            rust_code.append(stripped.replace("void ", "fn "))

        elif "alignas" in stripped:
            # Remove inline comments for processing
            stripped_no_comment = re.sub(r"//.*", "", stripped).strip()

            # Match alignas variable
            alignas_variable_pattern = re.match(
                r"alignas\(\s*(\d+)\s*\)\s*([\w\*]+)\s+(\w+)\s*;", 
                stripped_no_comment
            )

            # Match alignas array
            alignas_array_pattern = re.match(
                r"alignas\(\s*(\d+)\s*\)\s*([\w\*]+)\s+(\w+)\s*\[\s*(\d+)\s*\]\s*;", 
                stripped_no_comment
            )

            # Match alignas typedef
            alignas_typedef_pattern = re.match(
            r"using\s+(\w+)\s*=\s*alignas\((\d+)\)\s*(\w+);",
            stripped_no_comment)

            alignas_struct_pattern = re.match(
                r"alignas\((\d+)\)\s*struct\s*(\w+)\s*\{\s*((?:.|\n)*?)\s*\};",
                stripped_no_comment
            )
            rust_code = []

            if alignas_struct_pattern: #WILL ONLY WORK IF EVERYTHING IS IN ONE STRAIGHT LINE
                match = alignas_struct_pattern
                alignment = match.group(1)  # Extract the alignment value
                struct_name = match.group(2)  # Extract the struct name
                struct_body = match.group(3)  # Extract the fields within the struct

                # Process each field
                fields = struct_body.split(";")
                rust_fields = []
                for field in fields:
                    field = field.strip()
                    if field:  # Skip empty lines
                        parts = field.split()
                        if len(parts) >= 2:
                            c_type = parts[0]  # C++ type (e.g., int, double)
                            name = parts[1]  # Field name
                            rust_type_mapped = rust_type.get(c_type, f"/* Unsupported type: {c_type} */")
                            rust_fields.append(f"    {name}: {rust_type_mapped},")
                        else:
                            rust_fields.append(f"    /* Unsupported or malformed field: {field} */")

                # Construct the Rust struct
                rust_struct = f"#[repr(align({alignment}))]\nstruct {struct_name} {{\n" + "\n".join(rust_fields) + "\n}"
                rust_code.append(rust_struct)

            elif alignas_variable_pattern:
                rust_code.append("variabe")
                # Match variable alignment
                alignment, cpp_type, var_name = alignas_variable_pattern.groups()
                rust_type_map = {
                    "int": "i32",
                    "unsigned int": "u32",
                    "long": "i64",
                    "unsigned long": "u64",
                    "short": "i16",
                    "unsigned short": "u16",
                    "char": "char",
                    "unsigned char": "u8",
                    "bool": "bool",
                    "float": "f32",
                    "double": "f64",
                }
                rust_type = rust_type_map.get(cpp_type, None)
                if rust_type:
                    rust_code.append(f"#[repr(align({alignment}))]\nstruct S {{ {var_name}: {rust_type} }};")
                else:
                    rust_code.append(f"// Unsupported type in alignas variable: {cpp_type}")

            elif alignas_array_pattern:
                rust_code.append("array")
                # Match array alignment
                alignment, cpp_type, var_name, array_size = alignas_array_pattern.groups()
                rust_type_map = {
                    "int": "i32",
                    "unsigned int": "u32",
                    "long": "i64",
                    "unsigned long": "u64",
                    "short": "i16",
                    "unsigned short": "u16",
                    "char": "char",
                    "unsigned char": "u8",
                    "bool": "bool",
                    "float": "f32",
                    "double": "f64",
                }
                rust_type = rust_type_map.get(cpp_type, None)
                if rust_type:
                    rust_code.append(f"#[repr(align({alignment}))]\nstruct S {{ {var_name}: [{rust_type}; {array_size}] }};")
                else:
                    rust_code.append(f"// Unsupported type in alignas array: {cpp_type}")

            elif alignas_typedef_pattern:
                rust_code.append("typedef")
                # Match typedef/using alignment
                typedef_name, alignment, cpp_type = alignas_typedef_pattern.groups()
                rust_type_map = {
                    "int": "i32",
                    "unsigned int": "u32",
                    "long": "i64",
                    "unsigned long": "u64",
                    "short": "i16",
                    "unsigned short": "u16",
                    "char": "char",
                    "unsigned char": "u8",
                    "bool": "bool",
                    "float": "f32",
                    "double": "f64",
                }
                rust_type = rust_type_map.get(cpp_type, None)
                if rust_type:
                    rust_code.append(f"type {typedef_name} = #[repr(align({alignment}))] {rust_type};")
                else:
                    rust_code.append(f"// Unsupported type in alignas typedef: {cpp_type}")

            else:
                # Unrecognized alignas pattern
                rust_code.append(f"// Could not convert alignas statement: {stripped}")

        elif "alignof(" in stripped:
            alignof_pattern = re.match(r"alignof\((\w+)\)", stripped)
            if alignof_pattern:
                type_name = alignof_pattern.group(1)  # Extract the type inside alignof()
                rust_type = rust_type.get(type_name, None)
                rust_code.append(f"std::mem::align_of::<{rust_type}>();")
                continue
            else:
                rust_code.append(f"// Could not convert alignof statement: {stripped}")

        elif "compl" in stripped:
            stripped_no_comment = stripped.replace("compl ", "!")

        elif "concept" in stripped:
            stripped_no_comment = stripped.replace("concept", "trait")
        
        elif "const" in stripped:
            # Handle const member functions
            if re.search(r'\bconst\b\s*\(', stripped):
                stripped = stripped.replace("const", "") + " // const methods not directly supported in Rust"

            # Handle const variable declarations
            elif re.match(r'const\s+\w+\s+\w+', stripped):
                stripped_no_comment = re.sub(r'const\s+(\w+)\s+(\w+)', r'const \2: \1', stripped)

            # Handle const pointers (C++ specific, warn in Rust)
            elif re.search(r'\bconst\s+\*\s+', stripped):
                stripped = stripped.replace("const", "") + " // const pointers are not directly supported in Rust"

            # Handle const references (add comment as warning)
            elif re.search(r'\bconst\s+&\s+', stripped):
                stripped = stripped.replace("const", "") + " // const references are implicit in Rust"

            # Default case for other const usage
            else:
                stripped = stripped.replace("const", "// const equivalent may need manual adjustment in Rust")
            rust_code.append(stripped)

        elif re.match(r'^\s*template\s*<\s*(typename|class)\s+([\w, <>]+)\s*>', stripped):
            try:
                # Match template parameters
                template_match = re.match(r'^\s*template\s*<\s*(typename|class)\s+([\w, <>]+)\s*>', stripped)
                if template_match:
                    params = template_match.group(2).split(',')
                    rust_generics = [param.strip().replace("class", "").replace("typename", "").strip() for param in params]
                    rust_code.append(f"// Rust generics for template: <{', '.join(rust_generics)}>")
                # Check for specialization
                if "specialization" in stripped:
                    rust_code.append("// Note: Rust does not directly support template specializations.")
            except Exception as e:
                rust_code.append(f"// Error converting template: {e}")
                rust_code.append("// Original line: " + line)

        elif re.match(r'^\s*(\w+)<([\w, <>]+)>::(\w+)', stripped):
            try:
                # Match member function of a specialized template
                member_func_match = re.match(r'^\s*(\w+)<([\w, <>]+)>::(\w+)', stripped)
                if member_func_match:
                    class_name, specializations, method_name = member_func_match.groups()
                    rust_code.append(f"// Member function of specialized template: {class_name}<{specializations}>::{method_name}")
            except Exception as e:
                rust_code.append(f"// Error handling template member: {e}")
                rust_code.append("// Original line: " + line)

        elif re.match(r'^\s*typedef\s+(.+)\s+(\w+)\s*;', stripped):
            try:
                # Match typedef components
                typedef_match = re.match(r'^\s*typedef\s+(.+)\s+(\w+)\s*;', stripped)
                if typedef_match:
                    original_type, alias = typedef_match.groups()
                    rust_type_mapped = rust_type.get(original_type.strip(), f"/* Unsupported type: {original_type} */")
                    rust_code.append(f"type {alias} = {rust_type_mapped};")
            except Exception as e:
                rust_code.append(f"// Error converting typedef: {e}")
                rust_code.append("// Original line: " + line)
        elif re.search(r'typeid\s*\((.+?)\)', stripped):
            try:
                # Match typeid usage
                typeid_match = re.search(r'typeid\s*\((.+?)\)', stripped)
                if typeid_match:
                    type_expr = typeid_match.group(1)
                    rust_code.append(f"std::any::type_name::<{type_expr}>();")
            except Exception as e:
                rust_code.append(f"// Error converting typeid: {e}")
                rust_code.append("// Original line: " + line)
        elif re.match(r'^\s*typename\s+(\w+::\w+)', stripped):
            try:
                # Match typename usage
                typename_match = re.match(r'^\s*typename\s+(\w+::\w+)', stripped)
                if typename_match:
                    qualified_type = typename_match.group(1)
                    rust_code.append(f"// typename {qualified_type} resolved as {qualified_type}")
            except Exception as e:
                rust_code.append(f"// Error converting typename: {e}")
                rust_code.append("// Original line: " + line)
        elif "concept" in stripped:
            stripped_no_comment = stripped.replace("concept", "trait")
        elif "compl" in stripped:
            stripped_no_comment = stripped.replace("compl ", "!")
        elif "sizeof" in stripped:
            sizeof_match = re.search(r"sizeof\s*\((.*?)\)", stripped)
            if sizeof_match:
                rust_code.append(f"std::mem::size_of::<{sizeof_match.group(1)}>();")
        elif "consteval" in stripped:
            rust_code.append("// Rust does not have an equivalent for 'consteval'. Use 'const fn' for similar functionality.")

        elif "constexpr" in stripped:
            rust_code.append("// Replace 'constexpr' with 'const' or 'const fn' in Rust as appropriate.")

        elif "co_await" in stripped:
            rust_code.append("await")

        elif "decltype" in stripped:
            decltype_match = re.search(r"decltype\s*\((.*?)\)", stripped)
            if decltype_match:
                rust_code.append(f"std::any::type_name::<{decltype_match.group(1)}>();")

        elif "enum" in stripped:
            enum_match = re.match(r"enum\s+(\w+)\s*{", stripped)
            if enum_match:
                rust_code.append(f"enum {enum_match.group(1)} {{")
            elif stripped.strip() == "};":  # Handles end of enum
                rust_code.append("}")
            else:
                rust_code.append("// Enum detected. Translate cases manually.")

        elif "extern" in stripped:
            extern_match = re.match(r"extern\s+\"C\"\s*{", stripped)
            if extern_match:
                rust_code.append("extern \"C\" {")
            else:
                rust_code.append("// 'extern' detected. Translate manually for Rust external linkage.")

        elif "false" in stripped:
            rust_code.append(stripped.replace("false", "false"))

        elif "inline" in stripped:
            rust_code.append("// 'inline' functions are not explicitly declared in Rust. Simply omit 'inline'.")

        elif "namespace" in stripped:
            namespace_match = re.match(r"namespace\s+(\w+)\s*{", stripped)
            if namespace_match:
                rust_code.append(f"mod {namespace_match.group(1)} {{")
            else:
                rust_code.append("// 'namespace' detected. Translate to Rust 'mod' syntax.")

        elif "new" in stripped:
            new_match = re.search(r"new\s+(.+)", stripped)
            if new_match:
                rust_code.append(f"Box::new({new_match.group(1)})")

        elif "noexcept" in stripped:
            rust_code.append("// 'noexcept' has no equivalent in Rust. Ensure proper panic handling.")

        elif "nullptr" in stripped:
            rust_code.append(stripped.replace("nullptr", "None"))

        elif "operator" in stripped:
            rust_code.append("// 'operator' overloading must be manually converted to Rust trait implementations.")

        elif "reinterpret_cast" in stripped:
            reinterpret_match = re.search(r"reinterpret_cast<\s*(.+)\s*>\((.+)\)", stripped)
            if reinterpret_match:
                rust_code.append(f"({reinterpret_match.group(2)}) as {reinterpret_match.group(1)}")
            else:
                rust_code.append("// 'reinterpret_cast' detected. Translate manually.")

        elif "requires" in stripped:
            rust_code.append("// 'requires' should be translated to Rust's trait bounds or where clauses.")

        elif "signed" in stripped:
            rust_code.append("// 'signed' is implicit in Rust numeric types. No explicit keyword needed.")

        elif "sizeof" in stripped:
            sizeof_match = re.search(r"sizeof\s*\((.*?)\)", stripped)
            if sizeof_match:
                rust_code.append(f"std::mem::size_of::<{sizeof_match.group(1)}>();")

        elif "static_assert" in stripped:
            rust_code.append("// Replace 'static_assert' with a compile-time assert using 'const' in Rust.")

        elif "static_cast" in stripped:
            static_cast_match = re.search(r"static_cast<\s*(.+)\s*>\((.+)\)", stripped)
            if static_cast_match:
                rust_code.append(f"({static_cast_match.group(2)}) as {static_cast_match.group(1)}")
            else:
                rust_code.append("// 'static_cast' detected. Translate manually.")

        elif "try" in stripped and "catch" in stripped:
            rust_code.append("// 'try-catch' should be converted to Rust's 'Result' or 'Option'.")

        elif "virtual" in stripped:
            rust_code.append("// 'virtual' should be handled by implementing traits in Rust.")

        else:   
            rust_code.append(line)

    with open(output_file, "w") as rust_file:
        rust_file.write("\n".join(rust_code))