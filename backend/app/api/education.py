from typing import List
from fastapi import APIRouter, HTTPException
from ..schemas.education import (
    EducationModule, QuizQuestion, QuizOption, QuizSubmissionRequest,
    QuizSubmissionResponse, QuizQuestionResult
)

router = APIRouter()

EDUCATION_MODULES: List[EducationModule] = [
    EducationModule(
        id="phishing-fundamentals",
        title="Phishing & Credential Theft",
        category="Email & Messaging",
        difficulty="Beginner",
        summary="Learn how cybercriminals craft deceptive emails and login portals to harvest corporate and personal credentials.",
        key_indicators=[
            "Urgent deadlines or threats of account suspension within 24 hours.",
            "Generic greetings like 'Dear Customer' paired with requests to confirm passwords.",
            "Mismatched sender domain and Reply-To addresses.",
            "Unusual attachments requesting macro enablement (.docm, .xlsm, .iso, .zip)."
        ],
        prevention_tips=[
            "Inspect full sender email headers and domain spelling carefully.",
            "Never click links inside unprompted password reset or account verification emails.",
            "Navigate directly to the organization's official website via bookmarks or search.",
            "Enforce Hardware FIDO2 / WebAuthn MFA tokens to resist reverse-proxy phishing."
        ],
        real_world_example="An email spoofing Microsoft 365 security warns that your mailbox is full and redirects to a credential-harvesting replica page on a newly registered domain.",
        quizzes=[
            QuizQuestion(
                id="q1",
                question="You receive an email from 'support@paypa1-security.com' stating your account is frozen. What is the most significant indicator of phishing?",
                options=[
                    QuizOption(id="a", text="The email uses high-resolution logos."),
                    QuizOption(id="b", text="The domain uses typosquatting (number '1' replacing letter 'l')."),
                    QuizOption(id="c", text="The email was received on a weekday."),
                    QuizOption(id="d", text="The message has a footer with copyright information.")
                ],
                correct_option_id="b",
                explanation="The domain 'paypa1-security.com' is a classic typosquatting imitation replacing the letter 'l' with the numeral '1'."
            ),
            QuizQuestion(
                id="q2",
                question="What should you do if an email asks you to click a link to verify your corporate password?",
                options=[
                    QuizOption(id="a", text="Click the link immediately to prevent lockout."),
                    QuizOption(id="b", text="Forward the email to all colleagues to warn them."),
                    QuizOption(id="c", text="Report the email to your SOC / Security team without clicking the link."),
                    QuizOption(id="d", text="Reply with your old password asking if it is valid.")
                ],
                correct_option_id="c",
                explanation="Never click verification links in unsolicited emails. Immediately report the email to your security operations team."
            )
        ]
    ),
    EducationModule(
        id="quishing-qr-scams",
        title="QR Code Attacks (Quishing)",
        category="Mobile & Physical Vectors",
        difficulty="Intermediate",
        summary="Physical and digital QR codes bypass traditional email gateways because the URL is embedded in image pixels rather than text.",
        key_indicators=[
            "Physical stickers placed over legitimate parking meters, restaurant menus, or transit kiosks.",
            "Emails with no body text other than an embedded QR image asking you to scan with your phone.",
            "QR codes directing to shortened URLs or non-HTTPS destinations.",
            "Requests to input 2FA codes immediately after scanning."
        ],
        prevention_tips=[
            "Inspect physical QR stickers to verify they haven't been tampered with or placed over legitimate codes.",
            "Preview the destination URL on your phone camera app before opening.",
            "Use the ThreatLens QR analyzer to inspect destination URLs in a safe sandbox.",
            "Never approve MFA push notifications prompted immediately following a QR scan."
        ],
        real_world_example="Attackers stick fraudulent QR code labels on city parking payment meters, routing victims to lookalike payment sites to steal credit card details.",
        quizzes=[
            QuizQuestion(
                id="q3",
                question="Why do attackers use QR codes in email phishing campaigns?",
                options=[
                    QuizOption(id="a", text="QR codes load faster on slow internet connections."),
                    QuizOption(id="b", text="QR code URLs are rendered as images, evading standard text-based email security filters."),
                    QuizOption(id="c", text="QR codes are only readable by enterprise computers."),
                    QuizOption(id="d", text="QR codes guarantee that the destination is encrypted.")
                ],
                correct_option_id="b",
                explanation="Email security gateways typically parse plain text and HTML links. QR images hide the destination inside image pixels, often forcing victims onto unmanaged mobile devices."
            )
        ]
    ),
    EducationModule(
        id="suspicious-urls-punycode",
        title="URL Obfuscation & Punycode Homographs",
        category="Network & Web",
        difficulty="Advanced",
        summary="Attackers use internationalized domain names (IDN), double percent-encoding, and open redirects to deceive users and security scanners.",
        key_indicators=[
            "Domains starting with 'xn--' indicating Punycode international character encoding.",
            "Cyrillic characters (like 'а' U+0430) visually identical to Latin 'a' (U+0061).",
            "URLs with non-standard ports (e.g. :8443, :8080) or direct IP addresses.",
            "Unusual top-level domains like .top, .buzz, or .cfd."
        ],
        prevention_tips=[
            "Enable browser settings that display Punycode for non-native character domains.",
            "Avoid clicking links containing '@' separators in the URL authority section.",
            "Check for SSL certificate subject alternative names (SANs) matching the intended brand.",
            "Utilize threat intelligence engines to check domain registration age and reputation."
        ],
        real_world_example="A domain registered as 'xn--pple-43d.com' renders in some browsers as 'аpple.com' using a Cyrillic 'а', tricking users into believing it is Apple's legitimate portal.",
        quizzes=[
            QuizQuestion(
                id="q4",
                question="What is an IDN Homograph attack?",
                options=[
                    QuizOption(id="a", text="A brute force attack on DNS servers."),
                    QuizOption(id="b", text="An attack using lookalike Unicode glyphs from foreign alphabets to impersonate familiar domain names."),
                    QuizOption(id="c", text="Sending hundreds of emails from the same IP address."),
                    QuizOption(id="d", text="An SQL injection payload inside a URL query string.")
                ],
                correct_option_id="b",
                explanation="IDN Homograph attacks register domain names with characters from foreign alphabets (e.g. Cyrillic or Greek) that look identical to standard Latin characters."
            )
        ]
    ),
    EducationModule(
        id="otp-smishing-scams",
        title="SMS Phishing (Smishing) & OTP Theft",
        category="Mobile & Social",
        difficulty="Beginner",
        summary="Understand how smishing lures exploit urgency, delivery tracking, and bank fraud alerts to intercept SMS one-time passcodes.",
        key_indicators=[
            "SMS from unknown 10-digit numbers claiming to be major banks or shipping carriers.",
            "Urgent demands to reschedule package delivery by paying a small fee.",
            "Direct requests to reply with or enter an OTP code received on your device.",
            "Shortened URLs (bit.ly, tinyurl) in text messages."
        ],
        prevention_tips=[
            "Never share an OTP code with anyone over phone, SMS, or unverified websites.",
            "Legitimate banks will never ask you to read back a verification code.",
            "Track packages directly on official carrier apps rather than clicking SMS links.",
            "Switch to authenticator apps (TOTP) or hardware security keys over SMS verification."
        ],
        real_world_example="A text message claiming an undelivered USPS parcel asks you to pay a $1.50 redelivery fee, routing to a page that captures your payment card and prompts for the bank verification OTP.",
        quizzes=[
            QuizQuestion(
                id="q5",
                question="A caller claiming to be your bank's fraud department asks for the 6-digit code sent to your phone to 'cancel a suspicious transfer'. What should you do?",
                options=[
                    QuizOption(id="a", text="Provide the code so they can stop the fraudulent charge."),
                    QuizOption(id="b", text="Hang up immediately and call the official number on the back of your card."),
                    QuizOption(id="c", text="Give them the first 3 digits only."),
                    QuizOption(id="d", text="Ask them to email you a form instead.")
                ],
                correct_option_id="b",
                explanation="Legitimate financial institutions will never call asking for your incoming security OTP codes. Always hang up and dial the customer service number on the back of your card."
            )
        ]
    )
]

@router.get("/modules", response_model=List[EducationModule])
async def get_education_modules():
    """Returns all cybersecurity awareness and training modules."""
    return EDUCATION_MODULES

@router.get("/modules/{module_id}", response_model=EducationModule)
async def get_education_module(module_id: str):
    for mod in EDUCATION_MODULES:
        if mod.id == module_id:
            return mod
    raise HTTPException(status_code=404, detail="Education module not found")

@router.post("/quizzes/submit", response_model=QuizSubmissionResponse)
async def submit_quiz(req: QuizSubmissionRequest):
    """
    Evaluates quiz submissions and provides explainable answer feedback.
    """
    target_module = next((m for m in EDUCATION_MODULES if m.id == req.module_id), None)
    if not target_module:
        raise HTTPException(status_code=404, detail="Module not found")
        
    question_map = {q.id: q for q in target_module.quizzes}
    results: List[QuizQuestionResult] = []
    correct_count = 0
    
    for ans in req.answers:
        q = question_map.get(ans.question_id)
        if q:
            is_correct = (ans.selected_option_id == q.correct_option_id)
            if is_correct:
                correct_count += 1
            results.append(QuizQuestionResult(
                question_id=q.id,
                selected_option_id=ans.selected_option_id,
                correct_option_id=q.correct_option_id,
                is_correct=is_correct,
                explanation=q.explanation
            ))
            
    total = len(target_module.quizzes)
    pct = round((correct_count / total * 100), 1) if total > 0 else 100.0
    passed = pct >= 70.0
    
    return QuizSubmissionResponse(
        module_id=req.module_id,
        score=correct_count,
        total=total,
        percentage=pct,
        passed=passed,
        results=results
    )
