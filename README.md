🏋️‍♀️ CEO’muzun isteğini cevaplama zamanı!

## Problem

>❓ Olist, aşağıdakilere sahip olduğunu göz önünde bulundurduğunda, kârını artırmak için kaç tane düşük performans gösteren seller’ı sistemden çıkarmalıdır?
> - seller başına aylık bazı revenues
> - order başına bazı revenues
> - kötü review’lar başına (tahmini) bazı reputation costs
> - order item sayısıyla artan fakat lineer olmayan (scale effects) IT system operational costs

<details>
  <summary markdown='span'>💡 Hints</summary>
- Önce her order’ın review cost’unu hesaplayıp, daha sonra bu cost’ları seller bazında toplamayı isteyebilirsiniz.
</details>

## ✏️ Sıra sizde!

👉 **`CEO_request.ipynb` notebook’unu açın ve oradan başlayın.**

- Yeni bir Notebook ile başlayacağız
- Önceki notebook’ları yeniden kullanmayın – onlar yalnızca inceleme amacıyla hazırlanmıştı
- Yeniden kullanılabilir tüm logic’iniz `olist/*.py` script’lerinde kodlanmış durumda

## Çalışma Notları

Bu proje, her satıcının Olist'e net katkısını (gelir - yorum maliyeti - IT maliyeti) hesaplar ve en kötü N satıcıyı çıkarmanın kârı nasıl değiştirdiğini senaryolarla inceler. Analiz `CEO_request.ipynb` içinde sıfırdan kuruldu, yeniden kullanılabilir tüm kod `olist/` paketinde:

- `olist/data.py`: `data/` klasöründeki CSV dosyalarını okur.
- `olist/order.py`: `Order` sınıfı. Sipariş düzeyinde komisyon ve yorum maliyetini hesaplar (`get_order_items_economics`, `get_order_economics`), birden fazla satıcılı siparişlerde maliyeti ürün payına göre böler.
- `olist/seller.py`: `Seller` sınıfı. `get_training_data` her satır bir satıcı olan tabloyu döndürür: `revenues`, `cost_of_reviews`, `profits`, `revenue_per_month`, `operational_costs`, `net_contribution`.
- `olist/utils.py`: P&L parametreleri, IT maliyet fonksiyonu (`it_costs`) ve çıkarma senaryoları (`removal_scenarios`).

1. Ortam: `workintech` sanal ortamı. Proje klasöründe `pyenv local workintech` ile etkinleştirilir. `matplotlib` yoksa `pip install matplotlib` ile kurulur.
2. Olist veri setinin CSV dosyalarını (`olist_orders`, `olist_order_items`, `olist_order_reviews`, `olist_sellers`, `olist_customers`, `olist_geolocation`) `data/` klasörüne koy. CSV dosyaları `.gitignore` içindedir, repoda yoktur.
3. `jupyter notebook` ile `CEO_request.ipynb` dosyasını proje klasöründen aç ve hücreleri sırayla çalıştır. Tüm notebook birkaç saniyede çalışır.

Varsayımlar: teslim edilen siparişlerde ürün fiyatının %10'u komisyon, satıcı başına ayda 80 BRL abonelik, yorum maliyeti 1/2/3 yıldız için 100/50/40 BRL, IT maliyeti 3157.27 × √satıcı + 978.23 × √ürün (bugün 500 bin BRL).

Özet: Bugünkü kâr 729 bin BRL. Temel varsayımlarla optimum, en kötü 840 satıcıyı çıkarmak (+376 bin BRL, +%52), ama bu satılan ürünlerin %47'sini götürüyor ve yorum maliyetleri yarıya inerse kârı azaltıyor. Öneri: en kötü 18 satıcıyla başlamak. Bu adım kâr artışının yarısını getiriyor (+181 bin BRL) ve denenen 8 varsayım senaryosunun hepsinde kârlı. Kapsam en fazla 95 satıcıya kadar genişletilebilir. Bu 18 satıcı platformun en büyük satıcıları arasında (ürünlerin %16'sı), bu yüzden önce kalite planı, hedef tutmazsa çıkarma önerildi. Ayrıntılar ve sınırlılıklar notebook'un sonuç bölümünde.
