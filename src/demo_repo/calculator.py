"""Calculator module with intentional code quality issues."""

import math


def calc(a, b, op):
    """Do calculation."""
    if op == "add":
        return a + b
    elif op == "sub":
        return a - b
    elif op == "mul":
        return a * b
    elif op == "div":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    elif op == "pow":
        return a ** b
    elif op == "sqrt":
        if a < 0:
            raise ValueError("Cannot sqrt negative")
        return math.sqrt(a)
    elif op == "mod":
        return a % b
    elif op == "fact":
        if a < 0 or int(a) != a:
            raise ValueError("Factorial requires non-negative integer")
        result = 1
        for i in range(1, int(a) + 1):
            result = result * i
        return result
    elif op == "log":
        if a <= 0:
            raise ValueError("Log requires positive number")
        return math.log(a)
    elif op == "sin":
        return math.sin(a)
    elif op == "cos":
        return math.cos(a)
    elif op == "tan":
        return math.tan(a)
    elif op == "floor":
        return math.floor(a)
    elif op == "ceil":
        return math.ceil(a)
    elif op == "round":
        return round(a, int(b) if b else 0)
    else:
        raise ValueError(f"Unknown operation: {op}")


class DataProcessor:
    def __init__(self, data):
        self.data = data
        self.results = []
        self.temp = []
        self.flag = False
        self.count = 0
    
    def process(self):
        for item in self.data:
            if isinstance(item, int):
                if item > 0:
                    if item % 2 == 0:
                        self.results.append(item * 2)
                    else:
                        self.results.append(item * 3)
                else:
                    self.results.append(0)
            elif isinstance(item, str):
                if len(item) > 5:
                    self.results.append(item.upper())
                else:
                    self.results.append(item.lower())
            elif isinstance(item, float):
                self.results.append(round(item, 2))
            else:
                self.results.append(None)
            self.count += 1
        return self.results
    
    def get_stats(self):
        if not self.results:
            return {}
        total = 0
        valid = 0
        for r in self.results:
            if isinstance(r, (int, float)):
                total += r
                valid += 1
        return {"total": total, "count": valid, "avg": total / valid if valid else 0}


def legacy_api_fetch(url, params, headers, timeout, retries, backoff, verify_ssl, 
                     allow_redirects, proxies, auth, cookies):
    """Fetch data from API."""
    import requests
    import time
    
    last_error = None
    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
                verify=verify_ssl,
                allow_redirects=allow_redirects,
                proxies=proxies,
                auth=auth,
                cookies=cookies
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            elif response.status_code == 429:
                time.sleep(backoff * (attempt + 1))
                continue
            else:
                response.raise_for_status()
        except Exception as e:
            last_error = e
            time.sleep(backoff)
    
    raise last_error if last_error else Exception("All retries failed")
