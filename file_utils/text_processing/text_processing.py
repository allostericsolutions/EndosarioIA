import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s.]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def calculate_semantic_similarity(text1, text2):
    text1 = preprocess_text(text1)
    text2 = preprocess_text(text2)

    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()

    cosine_sim = cosine_similarity(vectors)
    return cosine_sim[0, 1] * 100

def extract_and_align_numbers_with_context(text1, text2, context_size=30):
    def extract_numbers_with_context(text):
        matches = re.finditer(r'\b\d+\b', text)
        numbers_with_context = []
        for match in matches:
            start = max(0, match.start() - context_size)
            end = min(len(text), match.end() + context_size)
            context = text[start:end].strip()
            numbers_with_context.append((match.group(), context))
        return numbers_with_context

    nums1_with_context = extract_numbers_with_context(text1)
    nums2_with_context = extract_numbers_with_context(text2)

    nums1 = [num for num, context in nums1_with_context] + [''] * max(0, len(nums2_with_context) - len(nums1_with_context))
    nums2 = [num for num, context in nums2_with_context] + [''] * max(0, len(nums1_with_context) - len(nums2_with_context))

    context1 = [context for num, context in nums1_with_context] + [''] * max(0, len(nums2_with_context) - len(nums1_with_context))
    context2 = [context for num, context in nums2_with_context] + [''] * max(0, len(nums1_with_context) - len(nums2_with_context))

    return ' '.join(nums1) if nums1 else 'N/A', ' '.join(context1) if context1 else 'N/A', ' '.join(nums2) if nums2 else 'N/A', ' '.join(context2) if context2 else 'N/A'

def calculate_numbers_similarity(nums1, nums2):
    nums1_list = nums1.split()
    nums2_list = nums2.split()
    matches = 0
    for n1, n2 in zip(nums1_list, nums2_list):
        if n1 == n2:
            matches += 1
    return (matches / len(nums1_list)) * 100 if nums1_list else 0
