from typing import List, Dict
from compiler_core.logging import log_step
from compiler_core.domain.tokens import Token
from compiler_core.domain.ast_nodes import ast_to_dict
from compiler_core.pipeline.lexer import lex
from compiler_core.pipeline import parser, semantics, ir, optimizer, codegen, peephole, vm
from compiler_core.repositories.compilation_run_repository import CompilationRunRepository


def token_to_json(t: Token) -> Dict:
    return {"type": t.type.name, "lexeme": t.lexeme, "line": t.line, "col": t.col}


class CompilerService:
    def compile(self, source: str, persist: bool = False):
        logs: List[str] = []
        def emit(msg):
            log_step(msg); logs.append(msg)

        # 01 Lexing
        emit('01. Lexical analysis started')
        tokens_objs = lex(source)
        tokens_json = [token_to_json(t) for t in tokens_objs]
        emit(f'01. Lexical analysis produced {len(tokens_json)} tokens')

        # 02 Parsing
        emit('02. Syntax analysis (parser) started')
        ast_root, parse_errors = parser.parse(tokens_objs)
        ast_json = ast_to_dict(ast_root)
        emit(f'02. Syntax analysis done with {len(parse_errors)} error(s)')

        # 03 Semantics
        emit('03. Semantic analysis started')
        sem = semantics.analyze(ast_root)
        typed_root = sem['typed_root']
        typed_json = sem['typed_json']
        emit(f"03. Semantic analysis done with {len(sem.get('errors', []))} error(s)")

        # 04 IR gen (stub)
        emit('04. IR generation started')
        ir_code = ir.ir_gen(typed_root)
        emit('04. IR generation done')

        # 05 IR opt (stub)
        emit('05. IR optimization started')
        ir_opt = optimizer.optimize_ir(ir_code)
        emit('05. IR optimization done')

        # 06 Codegen (stub)
        emit('06. Code generation started')
        bytecode = codegen.codegen(ir_opt)
        emit('06. Code generation done')

        # 07 Peephole (stub)
        emit('07. Machine-dependent peephole started')
        bytecode_opt = peephole.peephole(bytecode)
        emit('07. Peephole done')

        # 08 VM run (stub)
        emit('08. VM execution started')
        output = vm.run(bytecode_opt)
        emit('08. VM execution done')

        # Combine errors (parser + semantic)
        all_errors: List[Dict] = []
        all_errors.extend(parse_errors)
        all_errors.extend(sem.get('errors', []))

        result = {
            'stage_logs': logs,
            'errors': all_errors,
            'tokens': tokens_json,
            'ast': ast_json,
            'typed_ast': typed_json,
            'symbol_table': sem.get('symbol_table', {}),
            'ir': [str(x) for x in ir_code],
            'ir_optimized': [str(x) for x in ir_opt],
            'bytecode': [str(x) for x in bytecode],
            'bytecode_optimized': [str(x) for x in bytecode_opt],
            'output': output,
        }

        if persist:
            CompilationRunRepository().save_run(source, result)
        return result