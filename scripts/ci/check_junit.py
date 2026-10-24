import argparse
import json
import xml.etree.ElementTree as ET

parser=argparse.ArgumentParser()
parser.add_argument('path')
args=parser.parse_args()
root=ET.parse(args.path).getroot()
cases=list(root.iter('testcase'))
failures=list(root.iter('failure'))+list(root.iter('error'))
skips=list(root.iter('skipped'))
print(json.dumps({'tests':len(cases),'failures_errors':len(failures),'skips_xfails':len(skips)}))
if not cases or failures or skips:
    raise SystemExit('Suíte incompleta/falhou; skip/xfail não valida requisito obrigatório')
