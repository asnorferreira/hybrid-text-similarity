import json

from hts_core.adapters.semantic import prepare_cache

if __name__ == '__main__':
    print(json.dumps(prepare_cache(), indent=2))
