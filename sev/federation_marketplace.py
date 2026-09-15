from __future__ import annotations
from .trust_negotiation import TrustPolicy, negotiate

class FederationMarketplace:
    """Trust-aware bridge between a federation node and the local Skill marketplace.

    Artifacts stay quarantined until signature, origin policy, negotiated trust and
    security/certification checks succeed. The bridge deliberately never executes
    code during import; installation remains a separate policy-gated operation.
    """
    def __init__(self, marketplace, federation, network):
        self.marketplace=marketplace; self.federation=federation; self.network=network
    def import_skill(self, artifact, remote_policy=None, min_security=0.75):
        check=self.federation.signer.verify(artifact,self.federation.trusted_origins)
        if not check['valid']: raise ValueError(f"federation verification failed: {check['reason']}")
        policy=negotiate(self.network.policy, TrustPolicy(**(remote_policy or {})))
        if not policy['compatible']: raise ValueError('trust-policy-incompatible')
        payload=dict(artifact.get('payload') or {})
        if float(payload.get('security_rating',0)) < float(min_security):
            raise ValueError('security-rating-below-federation-policy')
        payload.update({'federation_origin':artifact.get('origin'),'provenance_status':'verified','federation_policy':policy['effective']})
        return self.marketplace.publish(payload)
