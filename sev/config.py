from __future__ import annotations
import json, os
from dataclasses import asdict, dataclass, field
from pathlib import Path

CONFIG_DIR = Path(os.environ.get('SKIF_CONFIG_DIR', Path.home() / '.skif'))
CONFIG_PATH = CONFIG_DIR / 'config.json'
ROLES = ('worker','critic','improver','judge','red_team','blue_team','reviewer')

@dataclass
class ProviderConfig:
    name: str
    kind: str
    model: str
    api_key_env: str = ''
    endpoint: str = ''
    api_compat: str = 'native'  # native|openai|anthropic
    max_tokens: int = 4096
    temperature: float | None = None
    input_cost_per_million: float = 0.0
    output_cost_per_million: float = 0.0
    headers: dict[str,str] = field(default_factory=dict)

@dataclass
class RoleConfig:
    providers: list[str] = field(default_factory=list)
    enabled: bool = True
    voting: bool = False
    vote_weight: float = 1.0
    provider: str = ''
    def __post_init__(self):
        if not self.providers and self.provider: self.providers=[self.provider]
        elif self.providers and not self.provider: self.provider=self.providers[0]

@dataclass
class BudgetConfig:
    max_candidates: int = 6
    max_parallel: int = 6
    max_generations: int = 2
    max_cases: int = 100
    max_tokens_per_run: int = 300000
    max_usd_per_run: float = 0.0

@dataclass
class CanaryConfig:
    enabled: bool = True
    stages: list[int] = field(default_factory=lambda:[1,5,25,50,100])
    require_approval: bool = True
    timeout_seconds: int = 900

@dataclass
class DeploymentConfig:
    enabled: bool = False
    command: str = ''
    smoke_test_command: str = ''
    rollback_command: str = ''
    require_approval: bool = True
    timeout_seconds: int = 900

@dataclass
class GitHubConfig:
    enabled: bool = False
    auto_pr: bool = False
    owner_repo: str = ''
    base_branch: str = 'main'
    token_env: str = 'GITHUB_TOKEN'
    draft_pr: bool = True
    gist_enabled: bool = True

@dataclass
class DatasetConfig:
    auto_generate_from_skills: bool = True
    cases_per_skill: int = 3
    protected: bool = True

@dataclass
class ShadowConfig:
    enabled: bool = True
    max_requests: int = 1000
    require_candidate_approval: bool = True
    max_mirrored_cost_usd: float = 0.0
    request_store: str = 'data/shadow/requests.jsonl'
    min_requests: int = 30
    alpha: float = 0.05
    significance_required: bool = True
    min_effect: float = 0.0
    production_mode: bool = True

@dataclass
class CompatibilityConfig:
    enabled: bool = True
    require_pass: bool = True
    max_regression: float = 0.0

@dataclass
class TelemetryConfig:
    enabled: bool = True
    store: str = 'data/events.db'
    retention_days: int = 90

@dataclass
class RuntimeConfig:
    mode: str = 'provider'  # provider|subprocess
    command: str = ''
    timeout_seconds: int = 900
    capture_tool_trace: bool = True

@dataclass
class ErrorReviewConfig:
    enabled: bool = True
    absolute_threshold: int = 5
    delta_threshold: float = 0.5
    window_minutes: int = 60
    auto_review: bool = True

@dataclass
class BattleConfig:
    enabled: bool = True
    red_team_rounds: int = 2
    blue_team_rounds: int = 2
    minimum_red_score: float = 0.5
    minimum_blue_score: float = 0.5

@dataclass
class MethodologyConfig:
    enabled: bool = True
    auto_collect: bool = True
    gist_publication: bool = False

@dataclass
class ProposalConfig:
    enabled: bool = True
    auto_publish_api: bool = True
    require_review: bool = True
    vote_threshold: float = 0.67


@dataclass
class ProductionConfig:
    kill_switch_path: str = 'data/production/kill_switch.json'
    deployment_lock_path: str = 'data/production/deploy.lock'
    dedupe_max: int = 1
    circuit_breaker_failures: int = 5
    circuit_breaker_reset_seconds: int = 60
    canary_min_sample: int = 10
    canary_max_error_rate: float = 0.05
    canary_max_latency_ratio: float = 1.25

@dataclass
class EvaluationIntelligenceConfig:
    mutation_enabled: bool = True
    mutations_per_case: int = 3
    hard_case_threshold: float = 0.6
    disagreement_threshold: float = 0.34
    duplicate_ratio_threshold: float = 0.2

@dataclass
class QueueConfig:
    enabled: bool = True
    workers: int = 2

@dataclass
class ReputationConfig:
    enabled: bool = True
    freshness_halflife_days: float = 30.0
    max_vote_weight: float = 2.0
    auto_approval_threshold: float = 0.92

@dataclass
class ResilienceConfig:
    enabled: bool = True
    max_agent_events_per_minute: int = 120
    max_agent_failures: int = 5
    block_seconds: int = 300
    max_request_bytes: int = 2_000_000
    max_global_events_per_minute: int = 2000

@dataclass
class KnowledgeConfig:
    enabled: bool = True
    path: str = 'data/knowledge.db'
    neighborhood_depth: int = 2

@dataclass
class MarketplaceConfig:
    enabled: bool = True
    path: str = 'data/marketplace'
    minimum_security: float = 0.75
    require_certification_for_install: bool = False

@dataclass
class FederationConfig:
    enabled: bool = True
    path: str = 'data/federation'
    origin: str = 'local'
    signing_key_env: str = 'SKIF_FEDERATION_KEY'
    trusted_origins: list[str] = field(default_factory=list)
    require_signed_artifacts: bool = True

@dataclass
class SecurityLabConfig:
    enabled: bool = True
    rounds: int = 2
    block_on_findings: bool = True
    max_payload_bytes: int = 2_000_000

@dataclass
class AuthConfig:
    host_token_env: str = 'SKIF_HOST_TOKEN'
    agent_token_env: str = 'SKIF_AGENT_TOKEN'
    user_token_env: str = 'SKIF_USER_TOKEN'
    require_host_dashboard_auth: bool = True
    require_agent_dashboard_auth: bool = True
    require_user_dashboard_auth: bool = True

@dataclass
class EvalCorpusConfig:
    root: str = 'data/eval_corpus'
    lifecycle_enforced: bool = True
    leakage_threshold: float = 0.92
    benchmark_path: str = 'data/benchmarks.jsonl'

@dataclass
class CacheConfig:
    enabled: bool = True
    ttl_seconds: float = 15.0
    max_items: int = 2048

@dataclass
class PerformanceConfig:
    benchmark_enabled: bool = True
    benchmark_iterations: int = 100
    max_api_latency_ms: float = 500.0

@dataclass
class SecurityHardeningConfig:
    continuous_fuzz_rounds: int = 3
    fuzz_mutations: int = 32
    require_quarantine_review: bool = True
    sandbox_commands_allowed: bool = False
    dependency_scan_enabled: bool = True
    attack_simulation_budget: int = 100

@dataclass
class FrameworkConfig:
    # 3.1 Neo runtime modes and host-level customization.
    providers: dict[str,ProviderConfig] = field(default_factory=dict)
    roles: dict[str,RoleConfig] = field(default_factory=lambda:{r:RoleConfig() for r in ROLES})
    submission_mode: str = 'feedback_or_patch'
    patch_mode: str = 'approval'
    alternatives: int = 3
    require_human_approval_to_promote: bool = True
    auto_promote: bool = False
    min_score_delta: float = 0.01
    max_regressions: int = 0
    preserve_mandatory_passes: bool = True
    use_git: bool = True
    create_worktrees: bool = True
    corpus_growth: bool = True
    convert_feedback_to_evals: bool = True
    voting_enabled: bool = True
    vote_mode: str = 'pairwise'  # pairwise|pointwise
    vote_threshold: float = 0.5
    pareto_enabled: bool = True
    pareto_require_quality_non_degrade: bool = True
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    shadow: ShadowConfig = field(default_factory=ShadowConfig)
    errors: ErrorReviewConfig = field(default_factory=ErrorReviewConfig)
    battle: BattleConfig = field(default_factory=BattleConfig)
    methodology: MethodologyConfig = field(default_factory=MethodologyConfig)
    proposals: ProposalConfig = field(default_factory=ProposalConfig)
    canary: CanaryConfig = field(default_factory=CanaryConfig)
    compatibility: CompatibilityConfig = field(default_factory=CompatibilityConfig)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    event_store: str = 'data/events.db'
    contribution_message_path: str = '.skif-contribution.md'
    judge_gold_suite: str = 'evals/gold.json'
    judge_min_calibration: float = 0.75
    autonomous_loops: int = 0
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    deployment: DeploymentConfig = field(default_factory=DeploymentConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    artifacts_dir: str = 'data/runs'
    registry_dir: str = 'data/registry'
    provenance_signing_key_env: str = ''
    api_token_env: str = 'SKIF_API_TOKEN'
    deployment_mode: str = 'personal'  # personal|federated
    node_id: str = 'local'
    host_custom: dict = field(default_factory=dict)
    agent_default_capabilities: list[str] = field(default_factory=lambda:['telemetry','feedback','vote','test'])
    prediction_market_enabled: bool = False
    resource_governance: dict = field(default_factory=lambda:{'max_usd':10.0,'max_tokens':100000,'max_seconds':900,'max_concurrent':4,'max_federation_bytes':10_000_000,'max_research_loops':4})
    plugin_allowlist: list[str] = field(default_factory=list)
    workspace_roots: list[str] = field(default_factory=list)
    production: ProductionConfig = field(default_factory=ProductionConfig)
    eval_intelligence: EvaluationIntelligenceConfig = field(default_factory=EvaluationIntelligenceConfig)
    queue: QueueConfig = field(default_factory=QueueConfig)
    reputation: ReputationConfig = field(default_factory=ReputationConfig)
    resilience: ResilienceConfig = field(default_factory=ResilienceConfig)
    knowledge: KnowledgeConfig = field(default_factory=KnowledgeConfig)
    marketplace: MarketplaceConfig = field(default_factory=MarketplaceConfig)
    federation: FederationConfig = field(default_factory=FederationConfig)
    security_lab: SecurityLabConfig = field(default_factory=SecurityLabConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    eval_corpus: EvalCorpusConfig = field(default_factory=EvalCorpusConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    security_hardening: SecurityHardeningConfig = field(default_factory=SecurityHardeningConfig)

    def to_json(self): return asdict(self)

def _role(raw):
    if 'providers' not in raw and raw.get('provider'): raw['providers']=[raw['provider']]
    return RoleConfig(providers=list(raw.get('providers',[])), enabled=bool(raw.get('enabled',True)), voting=bool(raw.get('voting',False)), vote_weight=float(raw.get('vote_weight',1.0)))

def _dc(cls, raw):
    return cls(**{k:v for k,v in (raw or {}).items() if k in cls.__annotations__})

def load_config() -> FrameworkConfig:
    if not CONFIG_PATH.exists(): return FrameworkConfig()
    raw=json.loads(CONFIG_PATH.read_text())
    providers={k:ProviderConfig(**v) for k,v in raw.get('providers',{}).items()}
    roles={r:_role(raw.get('roles',{}).get(r,{})) for r in ROLES}
    known={
        'submission_mode','patch_mode','alternatives','require_human_approval_to_promote','auto_promote','min_score_delta','max_regressions','preserve_mandatory_passes','use_git','create_worktrees','corpus_growth','convert_feedback_to_evals','voting_enabled','vote_mode','vote_threshold','pareto_enabled','pareto_require_quality_non_degrade',
        'event_store','artifacts_dir','registry_dir','contribution_message_path','judge_gold_suite','judge_min_calibration','autonomous_loops','provenance_signing_key_env','api_token_env','workspace_roots','deployment_mode','node_id','host_custom','agent_default_capabilities','prediction_market_enabled','resource_governance','plugin_allowlist'
    }
    kwargs={k:raw[k] for k in known if k in raw}
    kwargs.update({'providers':providers,'roles':roles})
    for name,cls in [('runtime',RuntimeConfig),('dataset',DatasetConfig),('shadow',ShadowConfig),('errors',ErrorReviewConfig),('battle',BattleConfig),('methodology',MethodologyConfig),('proposals',ProposalConfig),('canary',CanaryConfig),('compatibility',CompatibilityConfig),('telemetry',TelemetryConfig),('budget',BudgetConfig),('deployment',DeploymentConfig),('github',GitHubConfig),('production',ProductionConfig),('eval_intelligence',EvaluationIntelligenceConfig),('queue',QueueConfig),('reputation',ReputationConfig),('resilience',ResilienceConfig),('knowledge',KnowledgeConfig),('marketplace',MarketplaceConfig),('federation',FederationConfig),('security_lab',SecurityLabConfig),('auth',AuthConfig),('eval_corpus',EvalCorpusConfig),('cache',CacheConfig),('performance',PerformanceConfig),('security_hardening',SecurityHardeningConfig)]:
        kwargs[name]=_dc(cls,raw.get(name))
    return FrameworkConfig(**kwargs)

def save_config(c): CONFIG_DIR.mkdir(parents=True,exist_ok=True); CONFIG_PATH.write_text(json.dumps(c.to_json(),indent=2,ensure_ascii=False))
def get_api_key(p): return os.environ.get(p.api_key_env,'') if p.api_key_env else ''
