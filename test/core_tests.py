import sure
import contexts

core_file = repr(contexts.core.__file__)[1:-1]
this_file = repr(__file__)[1:-1]


class MockResult(object):
    def __init__(self):
        self.calls = []
        self.failed = False

    def suite_started(self, suite):
        self.calls.append(('suite_started', suite))

    def suite_ended(self, suite):
        self.calls.append(('suite_ended', suite))

    def context_started(self, context):
        self.calls.append(('context_started', context))

    def context_ended(self, context):
        self.calls.append(('context_ended', context))

    def context_errored(self, context, exception, extracted_traceback):
        self.calls.append(('context_errored', context, exception, extracted_traceback))

    def assertion_started(self, assertion):
        self.calls.append(('assertion_started', assertion))

    def assertion_passed(self, assertion):
        self.calls.append(('assertion_passed', assertion))

    def assertion_errored(self, assertion, exception, extracted_traceback):
        self.calls.append(('assertion_errored', assertion, exception, extracted_traceback))

    def assertion_failed(self, assertion, exception, extracted_traceback):
        self.calls.append(('assertion_failed', assertion, exception, extracted_traceback))


class WhenRunningASpec(object):
    def context(self):
        self.assertion_err = AssertionError()
        self.value_err = ValueError()

        class TestSpec(object):
            def __init__(s):
                s.log = ""
            def method_with_establish_in_the_name(s):
                s.log += "arrange "
            def method_with_because_in_the_name(s):
                s.log += "act "
            def method_with_should_in_the_name(s):
                s.log += "assert "
            def failing_method_with_should_in_the_name(s):
                s.log += "assert "
                raise self.assertion_err
            def erroring_method_with_should_in_the_name(s):
                s.log += "assert "
                raise self.value_err
            def method_with_cleanup_in_the_name(s):
                s.log += "teardown "

        self.spec = TestSpec()
        self.result = MockResult()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, self.result)

    def it_should_run_the_methods_in_the_correct_order(self):
        self.spec.log.should.equal("arrange act assert assert assert teardown ")

    def it_should_call_suite_started_first(self):
        self.result.calls[0][0].should.equal('suite_started')

    def it_should_call_ctx_started_second(self):
        self.result.calls[1][0].should.equal('context_started')

    def it_should_pass_in_the_ctx(self):
        self.result.calls[1][1].name.should.equal('TestSpec')

    def it_should_call_assertion_started_three_times(self):
        self.result.calls[2][0].should.equal('assertion_started')
        self.result.calls[4][0].should.equal('assertion_started')
        self.result.calls[6][0].should.equal('assertion_started')

    def it_should_call_assertion_passed_and_failed_and_errored(self):
        calls = [self.result.calls[i][0] for i in (3,5,7)]
        calls.should.contain('assertion_passed')
        calls.should.contain('assertion_failed')
        calls.should.contain('assertion_errored')

    def the_assertions_should_have_the_right_names(self):
        names = [self.result.calls[i][1].name for i in (3,5,7)]
        names.should.contain(__name__ + '.WhenRunningASpec.context.<locals>.TestSpec.method_with_should_in_the_name')
        names.should.contain(__name__ + '.WhenRunningASpec.context.<locals>.TestSpec.failing_method_with_should_in_the_name')
        names.should.contain(__name__ + '.WhenRunningASpec.context.<locals>.TestSpec.erroring_method_with_should_in_the_name')

    def it_should_pass_in_the_exceptions_and_tracebacks(self):
        error_infos = {}
        for i in (3,5,7):
            call_name = self.result.calls[i][0]
            if call_name == 'assertion_failed':
                error_infos['fail'] = (self.result.calls[i][2], self.result.calls[i][3])
            if call_name == 'assertion_errored':
                error_infos['error'] = (self.result.calls[i][2], self.result.calls[i][3])

        error_infos['fail'][0].should.equal(self.assertion_err)
        error_infos['fail'][1].should_not.be.empty
        error_infos['error'][0].should.equal(self.value_err)
        error_infos['error'][1].should_not.be.empty

    def it_should_call_ctx_ended_next(self):
        self.result.calls[8][0].should.equal('context_ended')

    def it_should_pass_in_the_ctx_again(self):
        self.result.calls[8][1].should.equal(self.result.calls[1][1])

    def it_should_call_suite_ended_last(self):
        self.result.calls[9][0].should.equal('suite_ended')

    def it_should_pass_in_the_same_suite_as_at_the_start(self):
        self.result.calls[9][1].should.equal(self.result.calls[0][1])

    def it_should_not_make_any_more_calls(self):
        self.result.calls.should.have.length_of(10)

class WhenAContextErrors(object):
    def context(self):
        class ErrorInSetup(object):
            def __init__(self):
                self.ran_cleanup = False
            def context(self):
                raise ValueError("explode")
            def it(self):
                pass
            def cleanup(self):
                self.ran_cleanup = True
        class ErrorInAction(object):
            def __init__(self):
                self.ran_cleanup = False
            def because(self):
                raise TypeError("oh no")
            def it(self):
                pass
            def cleanup(self):
                self.ran_cleanup = True
        class ErrorInTeardown(object):
            def it(self):
                pass
            def cleanup(self):
                raise AttributeError("got it wrong")

        self.specs = [ErrorInSetup(), ErrorInAction(), ErrorInTeardown()]

    def because_we_run_the_specs(self):
        self.results = []
        for spec in self.specs:
            result = contexts.reporting.SimpleResult()
            self.results.append(result)
            contexts.run(spec, result)

    def the_result_should_contain_the_setup_error(self):
        self.results[0].context_errors.should.have.length_of(1)

    def the_result_should_contain_the_action_error(self):
        self.results[1].context_errors.should.have.length_of(1)

    def the_result_should_contain_the_teardown_error(self):
        self.results[2].context_errors.should.have.length_of(1)

    def it_should_still_run_the_teardown_despite_the_setup_error(self):
        self.specs[0].ran_cleanup.should.be.true

    def it_should_still_run_the_teardown_despite_the_action_error(self):
        self.specs[1].ran_cleanup.should.be.true

class WhenWeRunSpecsWithAlternatelyNamedMethods(object):
    def context(self):
        class AlternatelyNamedMethods(object):
            def __init__(self):
                self.log = ""
            def has_context_in_the_name(self):
                self.log += "arrange "
            def has_when_in_the_name(self):
                self.log += "act "
            def has_it_in_the_name(self):
                self.log += "assert "
        class MoreAlternativeNames(object):
            def __init__(self):
                self.log = ""
            def has_since_in_the_name(self):
                self.log += "act "
            def has_must_in_the_name(self):
                self.log += "assert "
        class EvenMoreAlternativeNames(object):
            def __init__(self):
                self.log = ""
            def has_given_in_the_name(self):
                self.log += "arrange "
            def has_after_in_the_name(self):
                self.log += "act "
            def has_will_in_the_name(self):
                self.log += "assert "

        self.spec1 = AlternatelyNamedMethods()
        self.spec2 = MoreAlternativeNames()
        self.spec3 = EvenMoreAlternativeNames()

    def because_we_run_the_specs(self):
        contexts.run(self.spec1, contexts.reporting.SimpleResult())
        contexts.run(self.spec2, contexts.reporting.SimpleResult())
        contexts.run(self.spec3, contexts.reporting.SimpleResult())

    def it_should_run_the_methods_in_the_correct_order(self):
        self.spec1.log.should.equal("arrange act assert ")
        self.spec2.log.should.equal("act assert ")
        self.spec3.log.should.equal("arrange act assert ")

class WhenRunningAmbiguouslyNamedMethods(object):
    def context(self):
        class AmbiguousMethods1(object):
            def this_has_both_context_and_because_in_the_name(self):
                pass
        class AmbiguousMethods2(object):
            def this_has_both_because_and_should_in_the_name(self):
                pass
        class AmbiguousMethods3(object):
            def this_has_both_should_and_cleanup_in_the_name(self):
                pass
        class AmbiguousMethods4(object):
            def this_has_both_cleanup_and_establish_in_the_name(self):
                pass

        self.specs = [AmbiguousMethods1(), AmbiguousMethods2(), AmbiguousMethods3(), AmbiguousMethods4()]
        self.exceptions = []

    def because_we_try_to_run_the_specs(self):
        for spec in self.specs:
            self.exceptions.append(contexts.catch(lambda: contexts.run(spec, contexts.reporting.SimpleResult())))

    def it_should_raise_MethodNamingError(self):
        self.exceptions[0].should.be.a(contexts.errors.MethodNamingError)
        self.exceptions[1].should.be.a(contexts.errors.MethodNamingError)
        self.exceptions[2].should.be.a(contexts.errors.MethodNamingError)
        self.exceptions[3].should.be.a(contexts.errors.MethodNamingError)

class WhenRunningNotSoAmbiguouslyNamedMethods(object):
    def context(self):
        class NotAmbiguousMethods1(object):
            def this_has_both_context_and_establish_in_the_name(self):
                pass
        class NotAmbiguousMethods2(object):
            def this_has_both_because_and_when_in_the_name(self):
                pass
        class NotAmbiguousMethods3(object):
            def this_has_both_should_and_it_in_the_name(self):
                pass

        self.specs = [NotAmbiguousMethods1(), NotAmbiguousMethods2(), NotAmbiguousMethods3()]
        self.exceptions = []

    def because_we_try_to_run_the_specs(self):
        for spec in self.specs:
            self.exceptions.append(contexts.catch(lambda: contexts.run(spec, contexts.reporting.SimpleResult())))

    def it_should_not_raise_any_exceptions(self):
        self.exceptions[0].should.be.none
        self.exceptions[1].should.be.none
        self.exceptions[2].should.be.none

class WhenRunningSpecsWithTooManySpecialMethods(object):
    def context(self):
        class TooManyContexts(object):
            def context(self):
                pass
            def establish(self):
                pass
        class TooManyActions(object):
            def because(self):
                pass
            def when(self):
                pass
        class TooManyTeardowns(object):
            def cleanup1(self):
                pass
            def cleanup2(self):
                pass

        self.specs = [TooManyContexts(), TooManyActions(), TooManyTeardowns()]
        self.exceptions = []

    def because_we_try_to_run_the_specs(self):
        for spec in self.specs:
            self.exceptions.append(contexts.catch(lambda: contexts.run(spec, contexts.reporting.SimpleResult())))

    def it_should_raise_TooManySpecialMethodsError(self):
        self.exceptions[0].should.be.a(contexts.errors.TooManySpecialMethodsError)
        self.exceptions[1].should.be.a(contexts.errors.TooManySpecialMethodsError)
        self.exceptions[2].should.be.a(contexts.errors.TooManySpecialMethodsError)

class WhenCatchingAnException(object):
    def context(self):
        self.exception = ValueError("test exception")

        class TestSpec(object):
            def __init__(s):
                s.exception = None
            def context(s):
                def throwing_function(a, b, c, d=[]):
                    s.call_args = (a,b,c,d)
                    # Looks weird! Referencing 'self' from outer scope
                    raise self.exception
                s.throwing_function = throwing_function
            def should(s):
                s.exception = contexts.catch(s.throwing_function, 3, c='yes', b=None)

        self.spec = TestSpec()
        self.result = contexts.reporting.SimpleResult()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, self.result)

    def it_should_catch_and_return_the_exception(self):
        self.spec.exception.should.equal(self.exception)

    def it_should_call_it_with_the_supplied_arguments(self):
        self.spec.call_args.should.equal((3, None, 'yes', []))

    def it_should_not_have_a_failure_result(self):
        self.result.assertions.should.have.length_of(1)
        self.result.assertion_failures.should.be.empty
        self.result.context_errors.should.be.empty
        self.result.assertion_errors.should.be.empty

class WhenASpecHasASuperclass(object):
    def context(self):
        class SharedContext(object):
            def __init__(self):
                self.log = ""
            def context(self):
                self.log += "superclass arrange "
            def superclass_because(self):
                self.log += "superclass action "
            def it(self):
                self.log += "superclass assertion "
            def cleanup(self):
                self.log += "superclass cleanup "
        class Spec(SharedContext):
            # I want it to run the superclasses' specially-named methods
            # _even if_ they are masked by the subclass
            def context(self):
                self.log += "subclass arrange "
            def because(self):
                self.log += "subclass action "
            def it(self):
                self.log += "subclass assertion "
            def cleanup(self):
                self.log += "subclass cleanup "

        self.spec = Spec()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, contexts.reporting.SimpleResult())

    def it_should_run_the_superclass_setup_first(self):
        self.spec.log[:19].should.equal("superclass arrange ")

    def it_should_run_the_subclass_setup_next(self):
        self.spec.log[19:36].should.equal("subclass arrange ")

    def it_should_run_the_subclass_action_next(self):
        self.spec.log[36:52].should.equal("subclass action ")

    def it_should_not_run_the_superclass_action(self):
        self.spec.log.should_not.contain("superclass action ")

    def it_should_run_both_assertions(self):
        # We don't care what order the two assertions get run in
        self.spec.log[52:92].should.contain("superclass assertion ")
        self.spec.log[52:92].should.contain("subclass assertion ")

    def it_should_run_the_subclass_teardown_first(self):
        self.spec.log[92:109].should.equal("subclass cleanup ")

    def it_should_run_the_superclass_teardown_second(self):
        self.spec.log[109:238].should.equal("superclass cleanup ")

class WhenRunningAClass(object):
    def context(self):
        class TestSpec(object):
            was_run = False
            def it(self):
                self.__class__.was_run = True
        self.spec = TestSpec

    def because_we_run_the_class(self):
        contexts.run(self.spec, contexts.reporting.SimpleResult())

    def it_should_run_the_test(self):
        self.spec.was_run.should.be.true

class WhenRunningMultipleSpecs(object):
    def context(self):
        class Spec1(object):
            def it(self):
                self.was_run = True
        class Spec2(object):
            def it(self):
                self.was_run = True

        self.suite = [Spec1(), Spec2()]
        self.result = contexts.reporting.SimpleResult()

    def because_we_run_the_suite(self):
        contexts.run(self.suite, self.result)

    def it_should_run_both_tests(self):
        self.suite[0].was_run.should.be.true
        self.suite[1].was_run.should.be.true

    def the_result_should_have_two_ctxs(self):
        self.result.contexts.should.have.length_of(2)

    def the_result_should_have_two_assertions(self):
        self.result.assertions.should.have.length_of(2)

if __name__ == "__main__":
    contexts.main()
