"""Quick test for improved grammar checking without AI hallucinations."""
import asyncio
from services.checker import check_translation

async def test_grammar_checking():
    """Test the grammar checking - now WITHOUT AI hallucinations."""
    
    test_cases = [
        {
            "name": "❌ Двойной вспомогательный глагол (I'm + use)",
            "original_ru": "Я часто пользуюсь общественным транспортом.",
            "original_uz": "",
            "reference": "I often use public transport.",
            "user_answer": "I'm usually use public transport",
            "level": "B1",
            "expected_grammar": "30-50",
        },
        {
            "name": "❌ Неправильный предлог (in вместо at)",
            "original_ru": "Я обычно работаю по выходным.",
            "original_uz": "",
            "reference": "I usually work at weekends.",
            "user_answer": "I usually work in weekends",
            "level": "B1",
            "expected_grammar": "80-90",
        },
        {
            "name": "✅ Правильный ответ",
            "original_ru": "Я обычно работаю по выходным.",
            "original_uz": "",
            "reference": "I usually work at weekends.",
            "user_answer": "I usually work at weekends.",
            "level": "B1",
            "expected_grammar": "95-100",
        },
        {
            "name": "❌ Еще один двойной глагол (I'm work)",
            "original_ru": "Я работаю по выходным.",
            "original_uz": "",
            "reference": "I work on weekends.",
            "user_answer": "I'm work on weekends",
            "level": "A2",
            "expected_grammar": "40-60",
        },
        {
            "name": "❌ Present Continuous вместо Simple Present (are living)",
            "original_ru": "Мы живем в Ташкенте.",
            "original_uz": "",
            "reference": "We live in Tashkent.",
            "user_answer": "We are living in thashkent",
            "level": "B1",
            "expected_grammar": "50-65",
        },
    ]
    
    print("\n" + "="*80)
    print("🧪 GRAMMAR CHECKING TESTS (БЕЗ ИИ ГАЛЛЮЦИНАЦИЙ)")
    print("="*80)
    
    for test in test_cases:
        print(f"\n📝 {test['name']}")
        print(f"   Original RU: {test['original_ru']}")
        print(f"   Reference:  {test['reference']}")
        print(f"   User:       {test['user_answer']}")
        print(f"   Level:      {test['level']}")
        
        result = await check_translation(
            original_ru=test['original_ru'],
            original_uz=test['original_uz'],
            reference_english=test['reference'],
            user_answer=test['user_answer'],
            level=test['level'],
        )
        
        print(f"\n   📊 RESULTS:")
        print(f"      Syntax:   {result['details']['syntax']}/100 (ожидается: {test['expected_grammar']})")
        print(f"      Semantic: {result['details']['semantic']}/100")
        print(f"      TOTAL:    {result['score']}/100")
        
        if result['issues']:
            print(f"   ⚠️  ISSUES DETECTED:")
            for i, issue in enumerate(result['issues'], 1):
                print(f"      {i}. {issue}")
        else:
            print(f"   ✅ No issues detected")
        
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(test_grammar_checking())

