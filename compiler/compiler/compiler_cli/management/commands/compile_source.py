from django.core.management.base import BaseCommand, CommandError
from compiler_core.services.compiler_service import CompilerService

class Command(BaseCommand):
    help = 'Compile a source file (mini C++ subset) and print stage outputs.'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Path to source file')
        parser.add_argument('--persist', action='store_true', help='Save run in DB')

    def handle(self, *args, **options):
        path = options.get('file')
        if not path:
            raise CommandError('Please provide --file path to source code')
        with open(path, 'r', encoding='utf-8') as f:
            src = f.read()

        service = CompilerService()
        result = service.compile(src, persist=options.get('persist', False))

        self.stdout.write(self.style.SUCCESS('=== STAGE LOGS ==='))
        for line in result['stage_logs']:
            self.stdout.write(line)

        def section(title):
            self.stdout.write(self.style.SUCCESS(f'\n=== {title} ==='))

        section('ERRORS')
        if result.get('errors'):
            for e in result['errors']:
                self.stdout.write(f"Line {e.get('line')}:{e.get('col')} - {e.get('message')}")
        else:
            self.stdout.write('No errors')

        section('TOKENS')
        for t in result['tokens'][:200]:
            self.stdout.write(str(t))

        section('AST (parser JSON)')
        self.stdout.write(str(result['ast']))

        section('TYPED AST (with inferred types)')
        self.stdout.write(str(result['typed_ast']))

        section('SYMBOL TABLE')
        self.stdout.write(str(result['symbol_table']))

        section('IR (before opt)')
        for x in result['ir']:
            self.stdout.write(x)

        section('IR (after opt)')
        for x in result['ir_optimized']:
            self.stdout.write(x)

        section('BYTECODE (before peephole)')
        for x in result['bytecode']:
            self.stdout.write(x)

        section('BYTECODE (after peephole)')
        for x in result['bytecode_optimized']:
            self.stdout.write(x)

        section('PROGRAM OUTPUT')
        self.stdout.write(result['output'])