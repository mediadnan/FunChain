from time import sleep
from fastchain import Chain


def report_handler(report: dict) -> None:
    sleep(2)
    print(f"the success rate was {report['rate']:.2f}")


chain = Chain('test_chain', lambda x: x)
chain.add_report_handler(report_handler, True)
chain(3)
