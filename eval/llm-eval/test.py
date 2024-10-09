from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric, ContextualPrecisionMetric
from deepeval.test_case import LLMTestCase

# Set deppeval to use local model which in this case uses llama3.2 2B model
# deepeval set-local-model --model-name=llama3.2 --base-url="http://localhost:11434/v1/" --api-key="ollama"

def test_metrics(model_outputs, context, question):
    # Answer relevenacy metric
    answer_relevancy_metric = AnswerRelevancyMetric(
        threshold=0.7,
        include_reason=True
    )

    context_precision_metric = ContextualPrecisionMetric(
        threshold=0.7,
        include_reason=True
    )

    test_cases = []
    for model_output in model_outputs:
      test_case = LLMTestCase(
          input=question,
          actual_output=model_output,
          expected_output="Based on the context, there is no definition for impoldering available.",
          retrieval_context=[context],
      )
      test_cases.append(test_case)

    evaluate(test_cases, [answer_relevancy_metric, context_precision_metric], ignore_errors=True, use_cache=True)