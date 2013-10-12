import sys
import traceback
from .core import Result


class TextResult(Result):
    def __init__(self, stream=sys.stderr):
        self.stream = stream
        super().__init__()

    def _print(self, *args, sep=' ', end='\n', flush=True):
        print(*args, sep=sep, end=end, file=self.stream, flush=flush)

    def assertion_passed(self, *args, **kwargs):
        super().assertion_passed(*args, **kwargs)
        self._print('.', end='')

    def assertion_failed(self, *args, **kwargs):
        super().assertion_failed(*args, **kwargs)
        self._print('F', end='')

    def assertion_errored(self, *args, **kwargs):
        super().assertion_errored(*args, **kwargs)
        self._print('E', end='')

    def context_errored(self, *args, **kwargs):
        super().context_errored(*args, **kwargs)
        self._print('E', end='')

    def print_summary(self):
        self._print('')
        if self.failed:
            for tup in self.context_errors + self.assertion_errors + self.assertion_failures:
                self.print_assertion_failure(*tup)
        self._print("----------------------------------------------------------------------")
        if self.failed:
            self._print('FAILED!')
            self._print(self.failure_numbers())
        else:
            self._print('PASSED!')
            self._print(self.success_numbers())

    def print_assertion_failure(self, assertion, exception, extracted_tb):
        self._print("======================================================================")
        self._print("FAIL:" if isinstance(exception, AssertionError) else "ERROR:", assertion.name)
        self._print("----------------------------------------------------------------------")
        self._print("Traceback (most recent call last):")
        self._print(''.join(traceback.format_list(extracted_tb)), end='')
        self._print(''.join(traceback.format_exception_only(exception.__class__, exception)), end='')

    def success_numbers(self):
        num_ctx = len(self.contexts)
        num_ass = len(self.assertions)
        msg = "{}, {}".format(pluralise("context", num_ctx), pluralise("assertion", num_ass))
        return msg

    def failure_numbers(self):
        num_ctx = len(self.contexts)
        num_ass = len(self.assertions)
        num_ctx_err = len(self.context_errors)
        num_fail = len(self.assertion_failures)
        num_err = len(self.assertion_errors)
        msg =  "{}, {}: {} failed, {}".format(pluralise("context", num_ctx),
           pluralise("assertion", num_ass),
           num_fail,
           pluralise("error", num_err + num_ctx_err))
        return msg

def pluralise(noun, num):
    string = str(num) + ' ' + noun
    if num != 1:
        string += 's'
    return string
