##  Kullanılan Teknolojiler 

Yapay Zeka ve Veri İşleme (RAG Mimarisi)
* **[LangChain](https://www.langchain.com/)**
* **[ChromaDB](https://www.trychroma.com/)** 

Kullanılan Modeller
* **Embedding (Gömme) Modeli:** https://huggingface.co/Qwen/Qwen3-Embedding-0.6B 
* **Büyük Dil Modeli (LLM):** https://huggingface.co/meta-llama/Llama-3.1-8B

Kullanıcı Arayüzü (Frontend)
* **[React](https://react.dev/) & [Next.js](https://nextjs.org/):** 
* **[Tailwind CSS](https://tailwindcss.com/):** 


## ROADMAP V1
1) İndeksleme (Ingestion) pipeline’ını netleştirme
Yüklenen tüm dokümanları temiz metne çevirme, parçalara bölme (chunking), embedding, ChromaDB’ye yaz.
•	DOCX/PDF temizleme: başlıklar kalsın, gereksiz boşluk/tekrarlar gitsin.
•	Tablo dokümanlar: tabloyu “satır bazlı metin”e dönüştür (tarih–işlem eşleşmesi bozulmasın)
iye_surec_takvimi_2025-2026_Guz
•	Chunk boyutu: 300–600 token aralığı iyi olabilir.
•	Overlap: 50–100 token (maddeler bölünmesin diye).
Kritik: “Classroom duyuruları” gibi uzun blokları konu konu ayır; tek parça olarak embed etme.
2) Metadata stratejisi kurma
Chroma’ya her chunk için şu metadata’ları yaz:
•	source_type: yonerge / ek_form / sss / duyuru / takvim / akış
•	doc_name: dosya adı
•	section: başlık (varsa)
•	date veya term: (takvim/duyuru gibi)
•	audience: öğrenci / danışman / firma (bazen güzel filtre olur)
Bu sayede query geldiğinde:
•	“son tarih” sorularında source_type=takvim öncelikli aranır,
•	“EK-7 nasıl doldurulur?” sorusunda source_type=ek_form + yonerge öne alınır.
3) Intent detection + router’ı yaz
Önerilen intent’ler (örnek):
1.	selamlama
2.	sss_kisa (FAQ / kısa net cevaplar)
3.	takvim_tarih (son tarih, hangi gün, ne zaman)
4.	belge_form (EK-1, EK-7 nasıl doldurulur vs.)
5.	prosedur (başvuru süreci, protokol vs.)
6.	teknik_destek (yükleyemiyorum, site açılmıyor)
7.	out_of_scope (dokümanda yok / alakasız)
Router kararı:
•	selamlama/teknik_destek:  kural tabanlı
•	sss_kisa: önce JSON/FAQ matcher, bulamazsa RAG
•	takvim_tarih: RAG ama takvim filtresi/önceliğiyle
•	belge_form/prosedur: RAG (gerekirse multi-retrieval)
4) Doküman dışı bilgi üretmeyi engelle
•	Cevap formatı: “Kaynak + alıntı/parça + cevap”
•	Confidence check: Top-k retrieval skorları çok düşükse veya içerik soruyla alakasızsa:
o	“Bu bilgi sağlanan dokümanlarda bulunamadı.” deyip
o	kullanıcıya “hangi belgeyle ilgili?” gibi yönlendirme yap.
•	Sıkı sistem prompt: “Sadece verilen metinlere dayan, aksi halde ‘bulamadım’ de.”
UI’da kaynakar bölümü eklenebilir
5) Retrieval ayarları (LangChain tarafı)
İlk sürüm için pratik ayarlar:
•	similarity_search(k=4-6)
•	sonra MMR (max marginal relevance) dene (tekrar eden chunk’ları azaltır)
•	“takvim” sorularında k=8 iyi olabiliyor (çok tarih var)
Ayrıca iki aşamalı retrieval çok iyi sonuç verir:
1.	hızlı retrieval (k=12)
2.	rerank / filtreleme (en alakalı 4-6’yı LLM’e ver)
6) Test seti hazırla
20–40 soru yaz ve etiketle:
•	10 adet SSS
•	10 adet EK/form doldurma
•	10 adet takvim/son tarih
•	5 adet “dokümanda yok” (out-of-scope)
•	5 adet teknik/selamlama
Her soru için beklenen:
•	doğru intent
•	doğru kaynak doküman
•	doğru cevap / “bulamadım” davranışı
7) Frontend entegrasyonu (Next.js)
•	sohbet ekranı
•	“Kaynaklar” dropdown (cevabın dayandığı doküman parçaları)
•	geri bildirim: 👍👎 (“yanıt doğru mu?”)
•	“Bu cevap hangi dokümandan geldi?” link/etiket
Şu an gerekli 3 somut çıktı
1.	Ingestion scripti (dokümanları okuyup Chroma’yı oluşturan)
2.	Router (intent + rule-based + RAG) akışı
3.	Evaluation/test dosyası (20–40 soru)

EK ÖNERİLER:
1. Ingestion Aşaması: Tabloları "satır bazlı metin" yaparken, arka planda Markdown tablosu (| Tarih | İşlem |) formatına dönüştürmeyi dene. Modern LLM'ler Markdown yapılarını çok iyi anlar ve tarih-işlem eşleşmelerindeki kayıpları sıfıra indirir.
2. Intent Detection Aracı (Router Aşaması) Intent detection işlemi için LLM çağrısı yapmak sistemi yavaşlatabilir. Bunun yerine hafif bir NLP sınıflandırıcı (örneğin Hugging Face Zero-Shot Classification veya SetFit) ya da basit regex kuralları (özellikle takvim ve belge soruları için) kullanarak yönlendirmeyi çok daha hızlı yapabilirsin.
3. Reranker Seçimi (Retrieval Aşaması) İki aşamalı retrieval yaparken ikinci aşama (reranking) için açık kaynaklı ve hafif bir model olan bge-reranker (Hugging Face) kullanılabilir. "K=12 getir, en iyi 5'i LLM'e ver" mantığını kusursuz çalıştırır.
4. Test Seti Metrikleri (Evaluation Aşaması) Test setini manuel değerlendirmek yerine, RAGAS veya TruLens gibi RAG özelinde evaluation yapan kütüphanelere göz atılabilir. "Answer Relevance" (Cevap soruyla ne kadar alakalı?) ve "Context Precision" (Gelen doküman ne kadar doğru?) gibi istatistiksel metrikler sunulabilir.


Eğitim Dosyaları:
1- İş yeri eğitimi yönergesi. ✔✔✔YÜKLENDİ

2- EK dosyalarının hepsi. ✔✔✔YÜKLENDİ

3- 2025-2026 iş yeri eğitimi akış şeması ✔✔✔YÜKLENDİ

4- Marmara sayfasındaki soru cevaplar  ✔✔✔ YÜKLENDİ

5- Classroom toplantı notları ✔✔✔ YÜKLENDİ

6- CLASSROOM DUYURULARI ✔✔✔ YÜKLENDİ


