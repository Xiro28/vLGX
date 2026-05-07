from src.core.predicate.condition_cache import ConditionCache

class PredicateContainer:
    _predicates = list()

    @staticmethod
    def add_predicate(predicate: str):
        PredicateContainer._predicates.append(predicate)
        #we have to invalidate non-monotone caches because new facts can affect them
        ConditionCache.invalidate(monotone=False)

    @staticmethod
    def remove_predicate(predicate: str):
        PredicateContainer._predicates.remove(predicate)

        #here instead we invalidate both caches because removing a fact can affect both monotone and non-monotone conditions
        ConditionCache.invalidateAll()
        
    @staticmethod
    def get_predicate_value(predicate_head: str) -> list[str]:
        print(f"Searching for predicate with head '{predicate_head}' in container...")

        values = []
        for pred in PredicateContainer._predicates:
            if pred.startswith(predicate_head + "("):
                print(f"Found predicate '{pred}' matching head '{predicate_head}'")
                print(f"Extracting value from predicate: {pred}")
                values.append(pred.split("(", 1)[1].rsplit(")", 1)[0]) # Extract the value inside the parentheses
        return values if values else [""] # Return a list with an empty string if no values are found
    
    @staticmethod
    def get_all_values_for_predicate(predicate_head: str) -> str:
        values = ""
        for pred in PredicateContainer._predicates:
            if pred.startswith(predicate_head + "("):
                value = pred.split("(", 1)[1].rsplit(")", 1)[0]  # Extract the value inside the parentheses
                values += value + " "
        values = values.strip()  # Remove trailing space
        return values
    
    @staticmethod
    def reset_container():
        PredicateContainer._predicates = list()
        ConditionCache.clear()

    @staticmethod
    def get_all_predicates():
        return "\n".join(PredicateContainer._predicates)