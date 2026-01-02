# -*- coding: utf-8 -*-
"""
Created on Fri May 23 15:21:19 2025

@author: tceti
"""

import gradio  # Web arayüzlü uygulama için
import pyodbc  # SQL ile Python arasındaki bağlantıyı kurmak için 
from datetime import datetime  # bugünün tarihini otomatik almak için

# Veritabanına bağlanmak için bu bloğu kurduk. Kullanıcı adı şifre kullansaydım onları da girmemiz gerekecekti.
conn = pyodbc.connect( 
    'DRIVER={SQL Server};'
    'SERVER=TAHA\\SQLEXPRESS;'  
    'DATABASE=HastaRandevu;'
    'Trusted_Connection=yes;'
)
cursor = conn.cursor()

# Bu fonksiyon kullanıcının önce branşları görmesini sağlar. Yani branşları gösterir.
def branşları_getir():
    cursor.execute("SELECT Brans_ID, Brans_Adi FROM Brans")
    return cursor.fetchall()  # Tüm verileri çeker ve branşları listeye çevirir.

# Bu fonksiyon ise kullanıcının seçtiği branşın id’sini alır ve o id’ye ait doktorları girilen yazım şekline göre gösterir.
def doktorları_getir(brans_adi):
    cursor.execute("SELECT Brans_ID FROM Brans WHERE Brans_Adi = ?", (brans_adi,))
    brans_id = cursor.fetchone()[0]
    cursor.execute("SELECT Doktor_ID, Ad, Soyad FROM Doktor WHERE Brans_ID = ?", (brans_id,))
    return [f"{row[0]} - {row[1]} {row[2]}" for row in cursor.fetchall()]

# Burada kullanıcının aldığı randevu veritabanına kaydedilir ve tarih formatı kontrol edilir
def save_appointment(ad, soyad, tel, email, brans_adi, doktor_secimi, tarih_str, saat):
    # Tarih formatı kontrolü yapılır (hatalıysa uygulama çöker)
    datetime.strptime(tarih_str, "%Y-%m-%d")

    # Yeni hastayı ekler ve idsini alır çünkü randevu tablosunda kullanacağız.
    cursor.execute(
        "INSERT INTO Hasta (Ad, Soyad, Tel_No, Email) OUTPUT INSERTED.Hasta_ID VALUES (?, ?, ?, ?)",
        (ad, soyad, tel, email)
    )
    hasta_id = cursor.fetchone()[0]

    # Bu satır doktorun id'sini çeker    
    doktor_id = int(doktor_secimi.split(" - ")[0]) 

    # Randevu tablosuna kayıt ekler ve commit ile veritabanına eklenir
    cursor.execute(
        "INSERT INTO Randevu (Randevu_Tarihi, Randevu_Saati, Doktor_ID, Hasta_ID) VALUES (?, ?, ?, ?)",
        (tarih_str, saat, doktor_id, hasta_id)
    )
    conn.commit()

    return "Randevu kaydedildi."

# Dropdown’da göstermek için branş adlarını alır
branslar = branşları_getir()
branş_isimlerii = [row[1] for row in branslar]

# Bu kısımda gradio arayüzünün kullanıcının gördüğü kısmı düzenlemek için.
with gradio.Blocks() as app:
    gradio.Markdown("## HASTA RANDEVU ALMA UYGULAMASI")

    with gradio.Row():
        ad = gradio.Textbox(label="İSİM")
        soyad = gradio.Textbox(label="SOYİSİM")

    with gradio.Row():
        tel = gradio.Textbox(label="TELEFON NUMARASI")
        email = gradio.Textbox(label="E-MAİL")

    brans_dropdown = gradio.Dropdown(choices=branş_isimlerii, label="BRANŞ")

    doktor_dropdown = gradio.Dropdown(choices=[], label="DOKTOR")

    tarih = gradio.Textbox(label="RANDEVU TARİHİ (YYYY-AA-GG şeklinde giriniz.)")
    saat = gradio.Textbox(label="RANDEVU SAATİ (SS:DD Şeklinde giriniz.)")

    sonuç = gradio.Textbox(label="RANDEVU KAYIT DURUMU")

    submit_btn = gradio.Button("RANDEVUYU ONAYLA")

    # Branş değişince doktorlar listesini otomatik değiştirir.
    def doktorları_yenile(brans_adi):
        return gradio.update(choices=doktorları_getir(brans_adi))

    brans_dropdown.change(fn=doktorları_yenile, inputs=brans_dropdown, outputs=doktor_dropdown)

    # Butona basınca save_appointment fonksiyonu çalışır ve sonucu yazdırır
    submit_btn.click(
        fn=save_appointment,
        inputs=[ad, soyad, tel, email, brans_dropdown, doktor_dropdown, tarih, saat],
        outputs=sonuç
    )

app.launch()