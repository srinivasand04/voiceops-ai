import os

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import numpy as np
import torch
from torchcodec.decoders import AudioDecoder
from pyannote.audio import Pipeline
from sklearn.cluster import KMeans


AUDIO_FILE = r"D:\Study\Voice_AI\data\audio\customer_call_001.wav"


# Whisper results we already generated successfully
WHISPER_SEGMENTS = [
    (0.00, 10.00, "Hello, I am calling about an order. I placed a few days ago. I still haven't received it, but I was expecting it yesterday."),
    (10.00, 18.00, "I'm sorry for the delay. I can check the status of the order for you. Could you please give me your order number?"),
    (18.00, 25.00, "Yeah, the order number is ORD1045."),
    (25.00, 33.00, "Hey, thank you. Let me check that for you. I can see that page was shipped, but there was a delay with the delivery."),
    (33.00, 38.00, "Okay, but I really did it yesterday. Could you let me know when you'll receive it?"),
    (38.00, 44.00, "According to the latest update, it should arrive within the next two days. Sorry for the inconvenience."),
    (44.00, 50.00, "I don't want really another two days. Can I refund it instead?"),
    (50.00, 54.00, "Yes, I can help you with that. I can submit a refund request for order."),
    (54.00, 57.00, "Okay, please do that. Hello, I will let you refund."),
    (57.00, 62.00, "Once the refund is processed, it should appear in your account in seven business days."),
    (62.00, 66.00, "Okay, that's fine. Please go ahead with the refund."),
    (66.00, 71.00, "Stanley, I submitted the refund request. Is there anything I can help you with?"),
    (71.00, 75.00, "No, that's all. Thank you. You're welcome. Have a nice, good day."),
]


print("=" * 70)
print("VOICEOPS AI - UTTERANCE SPEAKER TEST")
print("=" * 70)

torch.set_num_threads(1)

try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass


print()
print("[1] Loading pyannote embedding model...")

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-community-1"
)

pipeline.embedding_batch_size = 1
pipeline.to(torch.device("cpu"))

print("Embedding model loaded.")


print()
print("[2] Loading audio...")

decoder = AudioDecoder(AUDIO_FILE)
audio = decoder.get_all_samples().data

sample_rate = 16000

print("Audio shape:", audio.shape)


print()
print("[3] Creating embedding for each Whisper utterance...")

embeddings = []

for i, (start_time, end_time, text) in enumerate(
    WHISPER_SEGMENTS,
    start=1
):

    start = int(start_time * sample_rate)
    end = int(end_time * sample_rate)

    chunk = audio[:, start:end]

    print(
        f"Utterance {i:02d}: "
        f"{start_time:5.1f}s -> {end_time:5.1f}s"
    )

    with torch.no_grad():
        embedding = pipeline._embedding(
            chunk.unsqueeze(0)
        )[0]

    embeddings.append(embedding)


E = np.asarray(embeddings)

print()
print("Embedding matrix:", E.shape)
print("Finite:", np.isfinite(E).all())


print()
print("[4] Clustering 13 utterances into 2 speakers...")

kmeans = KMeans(
    n_clusters=2,
    n_init=20,
    random_state=42,
)

labels = kmeans.fit_predict(E)


print()
print("=" * 70)
print("SPEAKER-ATTRIBUTED TRANSCRIPT")
print("=" * 70)

for (start, end, text), label in zip(
    WHISPER_SEGMENTS,
    labels
):

    print(
        f"[{start:5.1f}s -> {end:5.1f}s] "
        f"SPEAKER_{label:02d}: {text}"
    )


print()
print("=" * 70)
print("SPEAKER SEQUENCE")
print("=" * 70)

print(list(labels))


print()
print("TEST COMPLETE")
print("=" * 70)