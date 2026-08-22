import unittest

from scripts.question_policy import canonical_answer, user_verified_answer, validate_decision


class QuestionPolicyTests(unittest.TestCase):
    def test_original_with_literal_evidence_is_allowed(self):
        ctx={"question_text":"Es original?","product_description":"Producto 100% original JBL."}
        d={"risk":"LOW","answer":"Si, es original.","evidence":"Producto 100% original JBL."}
        self.assertEqual(validate_decision(d,ctx),(True,"verified"))

    def test_original_without_explicit_originality_is_blocked(self):
        ctx={"question_text":"Es original?","product_description":"Marca JBL, color negro."}
        d={"risk":"LOW","answer":"Si, es original.","evidence":"Marca JBL"}
        self.assertEqual(validate_decision(d,ctx)[1],"authenticity_not_proven")

    def test_app_with_literal_compatibility_is_allowed(self):
        ctx={"question_text":"Se conecta con la app?","product_description":"Compatible con la app JBL Portable."}
        d={"risk":"LOW","answer":"Si, es compatible.","evidence":"Compatible con la app JBL Portable."}
        self.assertEqual(validate_decision(d,ctx),(True,"verified"))

    def test_app_name_without_compatibility_is_blocked(self):
        ctx={"question_text":"Se conecta con la app?","product_description":"JBL Portable."}
        d={"risk":"LOW","answer":"Si, es compatible.","evidence":"JBL Portable."}
        self.assertEqual(validate_decision(d,ctx)[1],"app_compatibility_not_proven")

    def test_negative_originality_and_app_evidence_are_blocked(self):
        ctx={"question_text":"Es original?","product_description":"No es original."}
        d={"risk":"LOW","answer":"Si, es original.","evidence":"No es original."}
        self.assertEqual(validate_decision(d,ctx)[1],"authenticity_negative_evidence")
        ctx={"question_text":"Es compatible con la app?","product_description":"No es compatible con la app."}
        d={"risk":"LOW","answer":"Si es compatible.","evidence":"No es compatible con la app."}
        self.assertEqual(validate_decision(d,ctx)[1],"app_negative_evidence")

    def test_sensitive_answers_are_canonical(self):
        self.assertIn("producto es original",canonical_answer("Es original?"))
        self.assertIn("compatible con la aplicacion",canonical_answer("Se conecta con la app?"))
        self.assertIn("original y es compatible",canonical_answer("Es original y compatible con la app?"))
        self.assertIsNone(canonical_answer("Cuanto dura la bateria?"))

    def test_user_verified_accounts_always_affirm_originality(self):
        for account in ("LUISED","EDILBERTO"):
            for question in ("Es original?","Es clon?","Es replica o autentico?"):
                answer=user_verified_answer(account,question)
                self.assertIsNotNone(answer)
                self.assertIn("si, el producto es original",answer.lower())
        self.assertIsNone(user_verified_answer("ASVA","Es original?"))

    def test_user_verified_accounts_affirm_app_compatibility(self):
        answer=user_verified_answer("LUISED","Es original y conecta con la app?")
        self.assertIn("original y es compatible",answer.lower())

    def test_unrelated_or_missing_evidence_is_blocked(self):
        ctx={"question_text":"Cuanto dura la bateria?","product_description":"Hasta 7 horas."}
        self.assertEqual(validate_decision({"risk":"LOW","answer":"7 horas","evidence":"IP67"},ctx)[1],"evidence_not_grounded")
        self.assertEqual(validate_decision({"risk":"LOW","answer":"No se especifica","evidence":""},ctx)[1],"evidence_missing")

    def test_high_risk_and_long_answers_are_blocked(self):
        ctx={"question_text":"Dato?","product_description":"Dato confirmado."}
        self.assertEqual(validate_decision({"risk":"HIGH","answer":"Dato","evidence":"Dato confirmado."},ctx)[1],"risk_not_low")
        self.assertEqual(validate_decision({"risk":"LOW","answer":"x"*501,"evidence":"Dato confirmado."},ctx)[1],"answer_too_long")


if __name__ == "__main__":
    unittest.main()
