from __future__ import annotations
from .evaluation import corpus_profile,generate_mutations,find_hard_cases,disagreement_cases,validate_and_propose,counterfactual_report,semantic_signature

class EvaluationIntelligence:
    def profile(self,suite): return corpus_profile(suite)
    def mutate(self,suite,variants=None,max_per_case=3): return generate_mutations(suite,variants,max_per_case)
    def validate(self,cases): return validate_and_propose(cases)
    def hard_cases(self,results,threshold=.6): return find_hard_cases(results,threshold)
    def disagreements(self,ballots): return disagreement_cases(ballots)
    def counterfactual(self,before,after,changed_files): return counterfactual_report(before,after,changed_files)
    def duplicate_ratio(self,suite):
        sigs=[semantic_signature(c) for c in suite]
        return (len(sigs)-len(set(sigs)))/len(sigs) if sigs else 0.0
