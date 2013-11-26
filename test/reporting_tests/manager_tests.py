from unittest import mock
import sure
from contexts.reporting.shared import ReporterManager
from .. import tools


class WhenComposingReporters(object):
    @classmethod
    def examples(cls):
        yield "context_started", (tools.create_context("ctx"),)
        yield "context_ended", (tools.create_context("ctx"),)
        yield "context_errored", (tools.create_context("ctx"), tools.build_fake_exception([("", 0, "", "")]))
        yield "assertion_started", (tools.create_assertion("ass"),)
        yield "assertion_passed", (tools.create_assertion("ass"),)
        yield "assertion_failed", (tools.create_assertion("ass"), tools.build_fake_exception([("", 0, "", "")]))
        yield "assertion_errored", (tools.create_assertion("ass"), tools.build_fake_exception([("", 0, "", "")]))
        yield "unexpected_error", (tools.build_fake_exception([("", 0, "", "")]),)

    def establish_that_the_manager_contains_reporters(self, example):
        self.name, self.args = example
        self.mock_reporter1, self.mock_reporter2 = (mock.Mock(), mock.Mock())
        self.manager = ReporterManager(self.mock_reporter1, self.mock_reporter2)
        self.mock_suite = self.manager.suite_view_model = mock.Mock()

    def because_we_call_a_method_on_the_reporter(self, example):
        getattr(self.manager, self.name)(*self.args)

    def it_should_pass_the_arguments_to_the_same_method_in_the_first_mock(self):
        getattr(self.mock_reporter1, self.name).assert_called_once_with(*self.args)

    def it_should_pass_the_arguments_to_the_same_method_in_the_second_mock(self):
        getattr(self.mock_reporter2, self.name).assert_called_once_with(*self.args)

    def it_should_pass_the_arguments_to_the_same_method_in_the_suite_vm(self):
        getattr(self.mock_suite, self.name).assert_called_once_with(*self.args)


class WhenCallingSuiteStartedOrSuiteEnded(object):
    @classmethod
    def examples(cls):
        yield "suite_started", ("abc",)
        yield "suite_ended", ("suite",)

    def establish_that_the_manager_contains_reporters(self, example):
        self.name, self.args = example
        self.mock_reporter1, self.mock_reporter2 = (mock.Mock(), mock.Mock())
        self.manager = ReporterManager(self.mock_reporter1, self.mock_reporter2)
        self.mock_suite = self.manager.suite_view_model = mock.Mock()

    def because_we_call_a_method_on_the_reporter(self, example):
        getattr(self.manager, self.name)(*self.args)

    def it_should_pass_the_arguments_to_the_same_method_in_the_first_mock(self):
        getattr(self.mock_reporter1, self.name).assert_called_once_with(*self.args)

    def it_should_pass_the_arguments_to_the_same_method_in_the_second_mock(self):
        getattr(self.mock_reporter2, self.name).assert_called_once_with(*self.args)

    def it_should_not_call_the_suite_vm(self):
        self.mock_suite.mock_calls.should.be.empty


class WhenQueryingAFailedManager(object):
    def establish_that_the_manager_contains_a_failed_reporter(self):
        self.manager = ReporterManager(FakeFailedReporter(), FakePassingReporter(), FakeDontKnowReporter())

    def because_we_ask_if_the_run_failed(self):
        self.result = self.manager.failed

    def it_should_say_it_failed(self):
        self.result.should.be.true

class WhenQueryingAPassingManager(object):
    def establish_that_the_manager_contains_a_failed_reporter(self):
        self.manager = ReporterManager(FakePassingReporter(), FakePassingReporter(), FakeDontKnowReporter())

    def because_we_ask_if_the_run_failed(self):
        self.result = self.manager.failed

    def it_should_say_it_passed(self):
        self.result.should.be.false


###########################################################
# Test helpers
###########################################################

class FakeFailedReporter(object):
    def __init__(self):
        self.failed = True
class FakePassingReporter(object):
    def __init__(self):
        self.failed = False
class FakeDontKnowReporter(object):
    pass