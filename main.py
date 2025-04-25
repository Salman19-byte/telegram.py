from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from telethon.sync import TelegramClient
from telethon.tl.types import Channel, Chat
import asyncio
import os
import random

# Simpan API_ID, API_HASH, dan BOT_TOKEN di variabel lingkungan untuk keamanan
API_ID = int(os.getenv("API_ID", "23899821"))
API_HASH = os.getenv("API_HASH", "cf5e46488aa189b974c5ff1c3e89d123")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7811093006:AAEJPDcrCviK-RtwzD75mWHTxfrUdblmQNY")

bot = Client("broadcast_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Dictionary untuk menyimpan status pengguna
user_states = {}

@bot.on_message(filters.command("start") & filters.private)
async def start(_, msg: Message):
    await msg.reply(
        "✨ **SELAMAT DATANG DI UBOTMOON** ✨\n\n"
        "Apa itu Ubotmoon?\n\n"
"Ubotmoon adalah bot Telegram yang bantu kamu sebar promosi jualan ke banyak grup sekaligus, tanpa harus kirim satu-satu.\n\n"
"Lebih cepat ⚡, lebih praktis ✅, dan lebih hemat waktu ⏰!\n\n"
        "❓ contact owner @nanonakha0\n\n"
        "📢 Jangan lupa bergabung dengan channel kami: [@ubotmoon](https://t.me/ubotmoon)\n\n\n\n"
"KLIK /login untuk memulai USERBOTNYA"
    )

@bot.on_message(filters.command("login") & filters.private)
async def login_command(_, msg: Message):
    user_id = msg.from_user.id
    if user_id in user_states:
        try:
            await user_states[user_id].get("client", TelegramClient(None, API_ID, API_HASH)).disconnect()
        except:
            pass
        del user_states[user_id]

    client = TelegramClient(None, API_ID, API_HASH)
    await client.connect()

    user_states[user_id] = {
        "step": "get_phone",
        "client": client
    }
    await msg.reply("Masukkan nomor HP Anda (format internasional, contoh: +6281234567890):")

@bot.on_message(filters.text & filters.private)
async def handle_login_steps(_, msg: Message):
    user_id = msg.from_user.id
    if user_id not in user_states:
        return

    data = user_states[user_id]
    client = data.get("client")

    if data["step"] == "get_phone":
        data["phone"] = msg.text.strip()
        try:
            sent = await client.send_code_request(data["phone"])
            data["sent_code"] = sent
            data["step"] = "get_otp"
            await msg.reply("Kode OTP telah dikirim via Telegram. Masukkan OTP-nya:\n\n"
"MASUKAN KODE OTP WAJIB PAKE SPASI,CONTOH\n\n"
"[1 8 9 2 5]")
        except Exception as e:
            await msg.reply(f"Gagal mengirim OTP: {e}")
            await client.disconnect()
            del user_states[user_id]

    elif data["step"] == "get_otp":
        code = msg.text.strip()
        try:
            await client.sign_in(data["phone"], code)
            await msg.reply("Login berhasil!")

            # Proses daftar grup setelah berhasil login
            dialogs = await client.get_dialogs()
            groups = [d for d in dialogs if isinstance(d.entity, (Channel, Chat)) and (getattr(d.entity, "megagroup", False) or getattr(d.entity, "broadcast", False))]

            if not groups:
                await msg.reply("Tidak ada grup yang bisa dikirimi pesan.")
                await client.disconnect()
                del user_states[user_id]
                return

            list_grup = "\n".join([f"{i+1}. {g.name}" for i, g in enumerate(groups)])
            await msg.reply(
                f"Ditemukan {len(groups)} grup:\n\n{list_grup}\n\n"
                "Kirim nomor grup yang ingin dipilih (pisahkan dengan koma, contoh: 1,2,3)",
                parse_mode=None
            )

            data["groups"] = groups
            data["selected"] = []
            data["step"] = "select_group"

        except Exception as e:
            if "password" in str(e).lower():
                data["step"] = "get_2fa"
                await msg.reply("Akun ini memiliki verifikasi dua langkah. Silakan masukkan kata sandi akun Telegram Anda:")
            else:
                await msg.reply(f"Login gagal: {e}")
                await client.disconnect()
                del user_states[user_id]

    elif data["step"] == "get_2fa":
        try:
            await client.sign_in(password=msg.text.strip())
            await msg.reply("Login berhasil dengan 2FA!")

            # Proses daftar grup setelah berhasil login dengan 2FA
            dialogs = await client.get_dialogs()
            groups = [d for d in dialogs if isinstance(d.entity, (Channel, Chat)) and (getattr(d.entity, "megagroup", False) or getattr(d.entity, "broadcast", False))]

            if not groups:
                await msg.reply("Tidak ada grup yang bisa dikirimi pesan.")
                await client.disconnect()
                del user_states[user_id]
                return

            list_grup = "\n".join([f"{i+1}. {g.name}" for i, g in enumerate(groups)])
            await msg.reply(
                f"Ditemukan {len(groups)} grup:\n\n{list_grup}\n\n"
                "Kirim nomor grup yang ingin dipilih (pisahkan dengan koma, contoh: 1,2,3)",
                parse_mode=None
            )

            data["groups"] = groups
            data["selected"] = []
            data["step"] = "select_group"

        except Exception as e:
            await msg.reply(f"Password salah atau gagal login: {e}")
            await client.disconnect()
            del user_states[user_id]

    elif data["step"] == "select_group":
        try:
            # Proses input dari pengguna
            selected = list(map(int, msg.text.strip().split(",")))
            if len(selected) < 1:
                return await msg.reply("Minimal pilih 1 grup.")
            
            # Validasi indeks grup
            selected_idx = [i-1 for i in selected if 0 < i <= len(data["groups"])]
            if not selected_idx:
                return await msg.reply("Indeks grup tidak valid. Coba lagi dengan nomor grup yang benar.")
            
            # Simpan grup yang dipilih dan lanjutkan ke langkah berikutnya
            data["selected"] = selected_idx
            data["step"] = "choose_mode"
            return await msg.reply(
                "**Pilih mode kirim pesan:**\n"
                "`1` Kirim pesan teks manual\n"
                "`2` Forward pesan dari channel\n\n"
                "_Balas dengan angka 1 atau 2_"
            )
        except ValueError:
            # Jika input tidak valid
            return await msg.reply("Format salah. Gunakan format seperti: 1,2,3")

    elif data["step"] == "choose_mode":
        if msg.text == "1":
            data["step"] = "input_message"
            return await msg.reply("Kirim teks pesan yang ingin Anda sebarkan.")
        elif msg.text == "2":
            data["step"] = "input_forward"
            return await msg.reply("Silakan forward satu pesan dari channel yang ingin Anda broadcast.")
        else:
            return await msg.reply("Balas dengan angka `1` atau `2`.")

    elif data["step"] == "input_message":
        # Proses pesan manual
        text_message = msg.text.strip()
        if not text_message:
            return await msg.reply("Pesan tidak boleh kosong. Coba kirim lagi.")

        # Tambahkan watermark ke pesan manual
        watermark = "\n\n---\n📢 **Dikirim via UbotMoon** [@ubotmoon](https://t.me/ubotmoon)"
        text_message_with_watermark = text_message + watermark

        data["step"] = "broadcasting"
        data["text_message"] = text_message_with_watermark

        await msg.reply("Broadcast pesan manual dimulai...", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Stop Kirim", callback_data="stop")]
        ]))

        # Lakukan broadcast pesan manual
        success = 0
        while not data.get("stop"):
            for i in data["selected"]:
                group = data["groups"][i]
                if data.get("stop"):
                    break
                try:
                    await data["client"].send_message(
                        entity=group.id,
                        message=text_message_with_watermark
                    )
                    await msg.reply(f"{i+1}. {group.name} berhasil dikirim.")
                    success += 1
                except Exception as e:
                    await msg.reply(f"{i+1}. {group.name} gagal: {e}")
                await asyncio.sleep(random.randint(20, 40))

        await msg.reply(f"Broadcast dihentikan. Total berhasil dikirim: {success} pesan.")
        await data["client"].disconnect()
        del user_states[user_id]

    elif data["step"] == "input_forward":
        if not msg.forward_from_chat or not msg.forward_from_message_id:
            return await msg.reply("Kamu harus forward langsung dari channel (bukan copy-paste).")

        # Simpan informasi pesan yang di-forward
        data["step"] = "broadcasting"
        chat_id = msg.forward_from_chat.id
        msg_id = msg.forward_from_message_id

        data["forward_chat_id"] = chat_id
        data["forward_msg_id"] = msg_id

        await msg.reply("Forward broadcast dimulai...", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Stop Kirim", callback_data="stop")]
        ]))

        # Lakukan broadcast forward pesan dengan watermark
        success = 0
        while not data.get("stop"):
            for i in data["selected"]:
                group = data["groups"][i]
                if data.get("stop"):
                    break
                try:
                    # Forward pesan asli
                    forwarded_message = await data["client"].forward_messages(
                        entity=group.id,
                        from_peer=chat_id,
                        messages=msg_id
                    )

                    # Tambahkan watermark sebagai balasan ke pesan yang di-forward
                    watermark = "\n\n---\n📢 DIKIRIM OLEH @Ubotmoon_bot"
                    await data["client"].send_message(
                        entity=group.id,
                        message=watermark,
                        reply_to=forwarded_message.id
                    )

                    await msg.reply(f"{i+1}. {group.name} berhasil di-forward dengan watermark.")
                    success += 1
                except Exception as e:
                    await msg.reply(f"{i+1}. {group.name} gagal: {e}")
                await asyncio.sleep(random.randint(20, 40))

        await msg.reply(f"Broadcast dihentikan. Total berhasil di-forward: {success} pesan.")
        await data["client"].disconnect()
        del user_states[user_id]

@bot.on_callback_query(filters.regex("stop"))
async def stop_callback(_, cb):
    user_id = cb.from_user.id
    if user_id in user_states:
        user_states[user_id]["stop"] = True
        await cb.message.edit_text("Broadcast dihentikan.")
        await user_states[user_id]["client"].disconnect()
        del user_states[user_id]

bot.run()
  
