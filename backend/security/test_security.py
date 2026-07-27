"""
test_security.py — Unit tests for all Vishwas modules (finalized interfaces).
Consumes Aayat's device_trust output as a plain dict. SIM is out of the runtime
chain (inlined static block). Zero third-party deps.
Run: python test_security.py
"""
import unittest
from datetime import datetime, timezone

from security_rules import RISK_WEIGHTS, RISK_BANDS, Device
from behavior_engine import BehaviorEngine, BehaviorInput, BehaviorSignals
from risk_engine import (evaluate_risk, RiskEvaluationInput, EnvironmentInput,
                         _device_score, _confidence_modifier)
from challenge_engine import ChallengeEngine, ChallengeContext
from unknown_risk_handler import UnknownRiskHandler, UnknownRiskEvent, VALID_STATUS
from decision_engine import DecisionEngine, TransactionContext


def _now_ms(): return int(datetime.now(timezone.utc).timestamp()*1000)
N20 = [1492,879,2341,567,4321,1103,782,2253,917,1657,
       3402,451,2783,1231,893,3157,673,1987,2101,763]
_be = BehaviorEngine()

def signals(hour=14, amount=1250, median=1500, std=800, recip="mom@upi",
            known=("mom@upi",), ts=(), amts=tuple(N20), otp=4200):
    return _be.analyze(BehaviorInput(hour, amount, median, std, recip, list(known),
                                     list(ts), list(amts), otp))

def device(status="TRUSTED_DEVICE", confidence=100, age_days=100):
    """Aayat's device_trust.to_dict() shape."""
    return {"device_status": status, "device_confidence": confidence,
            "device_age_days": age_days, "security_signals": [status]}


class TestSecurityRules(unittest.TestCase):
    def test_risk_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(RISK_WEIGHTS.values()), 1.0, places=9)
    def test_four_decision_bands_exist(self):
        self.assertEqual(set(RISK_BANDS), {"ALLOW","WARN","CHALLENGE","BLOCK"})
    def test_sim_not_in_weights(self):
        # SIM removed from runtime chain -> no weight
        self.assertNotIn("sim", RISK_WEIGHTS)
    def test_device_status_penalty_ladder(self):
        p = Device.STATUS_PENALTY
        self.assertEqual(p["TRUSTED_DEVICE"], 0)
        self.assertTrue(p["KNOWN_DEVICE"] < p["INACTIVE_DEVICE"] < p["NEW_DEVICE"]
                        < p["SUSPICIOUS_DEVICE"] < p["ZERO_DAY_DEVICE"])


class TestBehavior(unittest.TestCase):
    def test_outputs_booleans_only(self):
        for v in signals().as_dict().values():
            self.assertIsInstance(v, bool)
    def test_night_owl_true_at_1am(self):
        self.assertTrue(signals(hour=1).night_owl)
    def test_amount_spike_detected(self):
        self.assertTrue(signals(amount=50000).amount_spike)
    def test_new_recipient_detected(self):
        self.assertTrue(signals(recip="x@upi", known=("a@upi",)).new_recipient)
    def test_clean_all_false(self):
        self.assertEqual(signals().active(), [])


class TestDeviceConsumption(unittest.TestCase):
    """Risk Engine fully consumes Aayat's device output: status + confidence."""
    def test_status_penalty_ladder(self):
        # confidence fixed at 50 (neutral) -> base penalties surface directly
        self.assertEqual(_device_score(device("TRUSTED_DEVICE", 50)), 0)
        self.assertEqual(_device_score(device("KNOWN_DEVICE", 50)), 10)
        self.assertEqual(_device_score(device("INACTIVE_DEVICE", 50)), 25)
        self.assertEqual(_device_score(device("NEW_DEVICE", 50)), 50)
        self.assertEqual(_device_score(device("SUSPICIOUS_DEVICE", 50)), 75)
        self.assertEqual(_device_score(device("ZERO_DAY_DEVICE", 50)), 95)
    def test_confidence_modifier_bounds(self):
        self.assertAlmostEqual(_confidence_modifier(50), 1.0, places=6)
        self.assertLess(_confidence_modifier(100), 1.0)   # high conf dampens
        self.assertGreater(_confidence_modifier(0), 1.0)  # low conf amplifies
    def test_high_confidence_lowers_new_device_risk(self):
        low  = _device_score(device("NEW_DEVICE", 0))     # amplified
        high = _device_score(device("NEW_DEVICE", 100))   # dampened
        self.assertGreater(low, high)
    def test_unknown_status_defaults_safely(self):
        self.assertEqual(_device_score(device("WEIRD_STATUS", 50)),
                         Device.STATUS_PENALTY_DEFAULT)
    def test_zero_day_device_scores_high(self):
        self.assertGreaterEqual(_device_score(device("ZERO_DAY_DEVICE", 5)), 90)


class TestRiskEngine(unittest.TestCase):
    def test_accepts_behavior_signals(self):
        inp = RiskEvaluationInput(behavior_signals=signals(),
            environment=EnvironmentInput("X","X",8*3600000,"HOME_WIFI"),
            device_trust=device())
        self.assertIsInstance(inp.behavior_signals, BehaviorSignals)
    def test_output_shape(self):
        out = evaluate_risk(RiskEvaluationInput(behavior_signals=signals(),
            environment=EnvironmentInput("X","X",8*3600000,"HOME_WIFI"),
            device_trust=device()))
        self.assertTrue(0 <= out.risk_score <= 100)
        self.assertIn("security_signals", out.__dict__)
    def test_sim_block_inlined_static(self):
        out = evaluate_risk(RiskEvaluationInput(behavior_signals=signals(),
            environment=EnvironmentInput("X","X",8*3600000,"HOME_WIFI"),
            device_trust=device()))
        sim = out.security_signals["sim"]
        self.assertEqual(sim, {"available": False, "sim_risk": 0,
                               "reason": "telecom_integration_unavailable"})
    def test_sim_not_in_sub_scores(self):
        out = evaluate_risk(RiskEvaluationInput(behavior_signals=signals(),
            environment=EnvironmentInput("X","X",8*3600000,"HOME_WIFI"),
            device_trust=device()))
        self.assertNotIn("sim", out.security_signals["sub_scores"])


class TestChallenge(unittest.TestCase):
    def setUp(self): self.e = ChallengeEngine()
    def test_takes_context_object(self):
        self.assertTrue(self.e.generate(ChallengeContext(active_behavior=["new_device"])).challenge_required)
    def test_never_outputs_decision(self):
        r = self.e.generate(ChallengeContext(active_behavior=["new_device"]))
        self.assertNotIn(r.challenge_type, ["ALLOW","WARN","CHALLENGE","BLOCK"])
    def test_trigger_signal_machine_readable(self):
        r = self.e.generate(ChallengeContext(active_behavior=["otp_distress"]))
        self.assertEqual(r.trigger_signal, "otp_distress")
        self.assertNotIn(" ", r.trigger_signal)
    def test_new_device_via_aayat_status(self):
        r = self.e.generate(ChallengeContext(active_behavior=["night_owl"],
                                             device={"device_status": "NEW_DEVICE"}))
        self.assertEqual(r.challenge_type, "DEVICE_CONFIRMATION")
        self.assertEqual(r.trigger_signal, "new_device")


class TestUnknownRisk(unittest.TestCase):
    def setUp(self): self.h = UnknownRiskHandler()
    def test_low_warns(self):
        self.assertEqual(self.h.handle(UnknownRiskEvent("UNKNOWN_RISK",0.55)).decision, "WARN")
    def test_medium_challenges(self):
        self.assertEqual(self.h.handle(UnknownRiskEvent("UNKNOWN_RISK",0.75)).decision, "CHALLENGE")
    def test_high_blocks(self):
        self.assertEqual(self.h.handle(UnknownRiskEvent("UNKNOWN_RISK",0.91)).decision, "BLOCK")
    def test_reason_code_machine_readable(self):
        d = self.h.handle(UnknownRiskEvent("UNKNOWN_RISK",0.91))
        self.assertEqual(d.reason_code, "UNKNOWN_RISK_HIGH")
    def test_invalid_status_raises(self):
        with self.assertRaises(ValueError):
            self.h.handle(UnknownRiskEvent("HELLO", 0.90))
    def test_valid_statuses(self):
        self.assertEqual(VALID_STATUS, {"NORMAL","ANOMALOUS","UNKNOWN_RISK"})
    def test_generates_audit(self):
        before = len(self.h.audit_log)
        self.h.handle(UnknownRiskEvent("UNKNOWN_RISK",0.91))
        self.assertEqual(len(self.h.audit_log), before+1)


class TestDecision(unittest.TestCase):
    def setUp(self): self.e = DecisionEngine()
    def _ctx(self, sig=None, ip="X", lastip="X", net="HOME_WIFI",
             dev="TRUSTED_DEVICE", conf=100, fraud=0.05, aiconf=0.80, ur=None, amount=1250):
        return TransactionContext("T","PSB1234567890",amount,"UPI",
            risk_input=RiskEvaluationInput(
                behavior_signals=sig or signals(),
                environment=EnvironmentInput(ip, lastip,
                    600000 if ip!=lastip else 8*3600000, net),
                device_trust=device(dev, conf),
                ai_fraud_probability=fraud, ai_confidence=aiconf),
            unknown_risk_event=ur)
    def test_one_of_four_states(self):
        self.assertIn(self.e.decide(self._ctx()).decision, ["ALLOW","WARN","CHALLENGE","BLOCK"])
    def test_clean_allows(self):
        self.assertEqual(self.e.decide(self._ctx()).decision, "ALLOW")
    def test_fraud_blocks(self):
        sig = signals(hour=1, amount=50000, recip="attacker@upi", known=("mom@upi",),
                      amts=[10000]*20, otp=1800,
                      ts=[_now_ms()-60000,_now_ms()-120000,_now_ms()-180000])
        d = self.e.decide(self._ctx(sig=sig, ip="Dubai", lastip="Ludhiana", net="VPN",
                                    dev="ZERO_DAY_DEVICE", conf=5, fraud=0.97, aiconf=0.95, amount=50000))
        self.assertEqual(d.decision, "BLOCK")
    def test_unknown_risk_forces_block(self):
        d = self.e.decide(self._ctx(ur=UnknownRiskEvent("UNKNOWN_RISK",0.91,"T")))
        self.assertEqual(d.decision, "BLOCK")
        self.assertTrue(d.unknown_risk_applied)
        self.assertEqual(d.unknown_risk_reason_code, "UNKNOWN_RISK_HIGH")
    def test_challenge_carries_full_details(self):
        sig = signals(hour=23, amount=14971, median=4500, std=2500, recip="vendor@neft",
                      known=("mom@upi",))
        d = self.e.decide(self._ctx(sig=sig, ip="Mumbai", lastip="Ludhiana", net="MOBILE_DATA",
                                    dev="NEW_DEVICE", conf=10, fraud=0.55, aiconf=0.75, amount=14971))
        if d.decision == "CHALLENGE":
            self.assertIsNotNone(d.challenge_details)
            self.assertIn("challenge_type", d.challenge_details)
            self.assertIn("trigger_signal", d.challenge_details)
    def test_account_masked(self):
        self.assertIn("****", self.e.decide(self._ctx()).account_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
