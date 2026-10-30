"""Causal and counterfactual model checks; not empirical human validation."""

from copy import deepcopy
from dataclasses import asdict, replace
import unittest

from humanity import Simulation
from humanity.engine.decision import decide
from humanity.engine.emotion import Dimensions, EMOTION_KEYS, decay, response
from humanity.engine.models import Emotions, Event
from humanity.engine.perception import appraise, observe_events, perceive


class EmotionModelTests(unittest.TestCase):
    def setUp(self):
        self.sim = Simulation("controlled-encounter", 3)
        self.actor, self.observer, self.other = self.sim.world.agents
        self.observer.emotions = Emotions(0, 0, 0, 0, 0)

    def test_five_emotions_and_appraisal_dependencies(self):
        self.assertEqual(EMOTION_KEYS, ("joy", "sadness", "fear", "anger", "disgust"))
        danger = Dimensions(loss=.7, threat=.8, blame=.9, control=.1)
        low = response(danger, .6)
        high = response(replace(danger, control=.9), .6)
        self.assertGreater(low.fear, high.fear)
        self.assertGreater(low.sadness, high.sadness)
        self.assertGreater(high.anger, low.anger)
        self.assertEqual(low.disgust, 0)
        self.assertGreater(response(replace(danger, violation=.8), .6).disgust, 0)
        self.assertGreater(response(Dimensions(benefit=.8), .6).joy, 0)

    def test_decay_is_time_based(self):
        once, split = Emotions(.8, .6, .4, .2, .1), Emotions(.8, .6, .4, .2, .1)
        decay(once, 4)
        for _ in range(4):
            decay(split)
        for key in EMOTION_KEYS:
            self.assertAlmostEqual(getattr(once, key), getattr(split, key))
        self.assertAlmostEqual(once.joy, .4)

    def test_moral_values_change_disgust_but_refusal_is_not_wrongdoing(self):
        a = self.observer
        event = Event("betrayal", 0, "betrayal", "دروغ آشکار", "local", self.actor.id, a.id)
        a.values.honesty = .1
        tolerant = appraise(a, event, self.actor)
        a.values.honesty = .95
        strict = appraise(a, event, self.actor)
        self.assertGreater(strict.feelings.disgust, tolerant.feelings.disgust)
        refusal = Event("refusal", 0, "rejection", "دعوت پذیرفته نشد", "local", a.id, self.actor.id)
        result = appraise(a, refusal, self.actor)
        self.assertEqual(result.feelings.disgust, 0)
        self.assertEqual(result.dimensions.blame, 0)

    def test_subject_private_state_is_not_visible(self):
        event = Event("help", 0, "help", "کمک", "local", self.actor.id, self.observer.id)
        before = asdict(appraise(self.observer, event, self.actor))
        self.actor.emotions = Emotions(1, 1, 1, 1, 1)
        self.actor.traits.empathy = 0
        self.actor.identity.role = "نقش دیگر"
        self.assertEqual(before, asdict(appraise(self.observer, event, self.actor)))

    def test_unfair_history_changes_feeling_without_inventing_guilt(self):
        a = self.observer
        a.values.achievement = 1
        a.values.fairness = 1
        a.traits.ambition = 1
        a.needs.esteem = .1
        event = Event("success", 0, "achievement", "پیشرفت", "public", self.actor.id)
        a.beliefs.fairness = .95
        hopeful = appraise(a, event, self.actor)
        a.beliefs.fairness = .05
        doubtful = appraise(a, event, self.actor)
        self.assertGreater(doubtful.feelings.sadness, hopeful.feelings.sadness)
        self.assertEqual(doubtful.dimensions.blame, 0)
        self.assertEqual(doubtful.feelings.disgust, 0)

    def test_experience_changes_next_appraisal_and_directed_trust(self):
        a, b = self.actor, self.observer
        event = Event("harm", 0, "betrayal", "دروغ آشکار", "local", a.id, b.id)
        before = appraise(b, event, a)
        reverse = a.relationships[b.id].trust
        for _ in range(6):
            perceive(self.sim.world, b, event)
        after = appraise(b, event, a)
        self.assertGreater(after.dimensions.threat, before.dimensions.threat)
        self.assertGreater(b.relationships[a.id].resentment, 0)
        self.assertEqual(a.relationships[b.id].trust, reverse)

    def test_experience_changes_actual_next_decision(self):
        a = self.observer
        a.traits.self_control = .1
        a.needs.energy = .9
        a.needs.belonging = .9
        before = deepcopy(a)
        event = Event("harm", 0, "conflict", "اختلاف", "local", self.actor.id, a.id)
        for _ in range(12):
            perceive(self.sim.world, a, event)
        # Hold random state fixed so only the experience changes the policy.
        rng = self.sim.world.rng
        first = decide(self.sim.world, before)
        self.sim.world.rng = rng
        second = decide(self.sim.world, a)
        self.assertNotEqual(first.action_id, second.action_id)
        self.assertTrue(any("خشم" in f.label or "ترس" in f.label or "عاطفی" in f.label for f in second.factors))

    def test_trace_and_bounded_reaction_chain(self):
        event = self.sim.encounter("insult", self.actor.id, self.observer.id)
        memory = next(m for m in reversed(self.observer.memories) if m.event_id == event.id)
        self.assertEqual(set(memory.emotions_before), set(EMOTION_KEYS))
        self.assertGreater(memory.emotions_after["disgust"], memory.emotions_before["disgust"])
        self.assertTrue(memory.reaction_reason)
        replies = self.sim.world.pending_events[:]
        self.assertTrue(replies)
        self.assertTrue(all(e.kind == "response" and "causeId" in e.change for e in replies))
        observe_events(self.sim.world)
        self.assertEqual(self.sim.world.pending_events, [])
        self.assertTrue(any(e.observers for e in replies))

    def test_existing_joy_does_not_turn_an_insult_into_thanks(self):
        self.observer.emotions.joy = .9
        self.observer.values.care = .9
        self.observer.values.fairness = .9
        event = self.sim.encounter("insult", self.actor.id, self.observer.id)
        memory = next(m for m in self.observer.memories if m.event_id == event.id)
        self.assertEqual(memory.expression, "withdraw")
        self.assertEqual(self.observer.extensions["emotionModel"]["memoryId"], memory.id)

    def test_conditions_do_not_set_everyones_emotions_to_the_same_number(self):
        initial = self.sim.snapshot()
        safe, harsh = Simulation.from_snapshot(initial), Simulation.from_snapshot(initial)
        for sim, safety in ((safe, .95), (harsh, .05)):
            sim.set_condition("social_safety", safety)
            sim.step()
        safe_fear = sum(a.emotions.fear for a in safe.world.agents)
        harsh_fear = sum(a.emotions.fear for a in harsh.world.agents)
        self.assertGreater(harsh_fear, safe_fear)
        self.assertGreater(len({round(a.emotions.fear, 5) for a in harsh.world.agents}), 1)
        self.assertTrue(all(any(m.kind == "appraisal" and "شرایط" in m.text for m in a.memories) for a in harsh.world.agents))


if __name__ == "__main__":
    unittest.main()
