from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out_dir = Path(__file__).resolve().parents[1] / 'docs' / 'screenshots'
out_dir.mkdir(parents=True, exist_ok=True)


def font(size, bold=False):
    candidates = [
        'C:/Windows/Fonts/arialbd.ttf',
        'C:/Windows/Fonts/segoeui.ttf',
        'C:/Windows/Fonts/segoeuib.ttf',
        'C:/Windows/Fonts/calibri.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    for path in candidates:
        try:
            if bold:
                return ImageFont.truetype(path.replace('Sans', 'Sans-Bold') if 'DejaVu' in path and 'Bold' not in path else path, size)
            return ImageFont.truetype(path, size=size)
        except Exception:
            pass
    return ImageFont.load_default()

# Login screen
img = Image.new('RGB', (1200, 900), '#F5F7FB')
d = ImageDraw.Draw(img)
for y in range(0, 900, 42):
    d.line((0, y, 1200, y), fill=(238, 242, 250), width=1)
# logo
logo_box = (510, 80, 690, 260)
d.rounded_rectangle(logo_box, radius=28, fill='#4F46E5')
d.ellipse((560, 140, 640, 220), fill='#7DD3FC')
d.rounded_rectangle((585, 150, 620, 188), radius=10, fill='white')
d.ellipse((595, 160, 610, 175), fill='#F59E0B')
# title
font_big = font(56, bold=True)
font_mid = font(26)
font_label = font(20, bold=True)
d.text((600, 300), 'FindBack AI', fill='#111827', font=font_big, anchor='mm')
d.text((600, 355), 'AI-powered lost & found for your campus', fill='#5B6475', font=font_mid, anchor='mm')
# form
card = (170, 390, 1030, 760)
d.rounded_rectangle(card, radius=18, fill='white', outline='#E5E7EB', width=2)
d.text((220, 430), 'Sign in to your account', fill='#111827', font=font(32, bold=True))
for idx, label in enumerate(['Username', 'Password']):
    y = 490 + idx * 140
    d.text((220, y), label, fill='#334155', font=font_label)
    d.rounded_rectangle((220, y + 28, 900, y + 92), radius=10, fill='#F3F4F6', outline='#D9DEE8')
    if label == 'Username':
        d.text((240, y + 42), 'e.g. user1', fill='#6B7280', font=font(22))
    else:
        d.text((240, y + 42), '••••••••', fill='#6B7280', font=font(24))
        d.ellipse((840, y + 40, 872, y + 72), outline='#4B5563', width=2)

d.rounded_rectangle((220, 670, 900, 720), radius=12, fill='#F3F4F6', outline='#E5E7EB')
d.text((560, 695), 'Sign In', fill='#111827', font=font(28, bold=True), anchor='mm')
# demo area
box = (220, 770, 900, 850)
d.rounded_rectangle(box, radius=12, fill='#F3F4F6', outline='#E5E7EB')
d.text((245, 790), 'Demo accounts', fill='#111827', font=font(20, bold=True))
d.text((245, 822), 'admin / Admin@123   staff / Staff@123', fill='#475569', font=font(18))
img.save(out_dir / 'login-screen.png')

# Match results
img = Image.new('RGB', (1200, 900), '#F5F7FB')
d = ImageDraw.Draw(img)
d.rounded_rectangle((60, 50, 1140, 850), radius=22, fill='white', outline='#E5E7EB', width=2)
d.text((120, 90), 'Find Matches', fill='#111827', font=font(40, bold=True))
d.rounded_rectangle((120, 150, 1080, 220), radius=14, fill='#F3F4F6', outline='#E5E7EB')
d.text((145, 172), 'Selected lost item', fill='#475569', font=font(18, bold=True))
d.text((145, 198), '#12 Black Wallet - Library', fill='#111827', font=font(22))
for i, data in enumerate([
    ('Black Wallet', 'Sarah Khan (sarah)', 'John Smith (john)'),
    ('Leather Card Holder', 'Ayesha Ali (ayesha)', 'Ali Khan (ali)'),
    ('Travel Wallet', 'Hamza Tariq (hamza)', 'Noor Ahmed (noor)')
]):
    y = 260 + i * 175
    d.rounded_rectangle((120, y, 1080, y + 120), radius=18, fill='#F9FAFB', outline='#E5E7EB')
    d.rounded_rectangle((150, y + 18, 300, y + 118), radius=14, fill='#E2E8F0')
    d.text((225, y + 70), 'IMG', fill='#475569', font=font(24, bold=True), anchor='mm')
    d.text((330, y + 28), data[0], fill='#111827', font=font(26, bold=True))
    d.text((330, y + 58), f'Reported by: {data[1]}', fill='#52607A', font=font(18))
    d.text((330, y + 82), f'Lost item reported by: {data[2]}', fill='#52607A', font=font(18))
    d.rounded_rectangle((810, y + 30, 1035, y + 46), radius=8, fill='#4F46E5')
    d.text((925, y + 58), '92% Strong Match', fill='#1F2937', font=font(20, bold=True), anchor='mm')
img.save(out_dir / 'match-results.png')

# User management
img = Image.new('RGB', (1200, 900), '#F5F7FB')
d = ImageDraw.Draw(img)
d.rounded_rectangle((70, 55, 1130, 840), radius=22, fill='white', outline='#E5E7EB', width=2)
d.text((120, 95), 'User Management', fill='#111827', font=font(38, bold=True))
headers = ['Name', 'Username', 'Email', 'Role']
positions = [(120, 160), (360, 160), (560, 160), (880, 160)]
for x,label in zip([120,360,560,880], headers):
    d.rounded_rectangle((x, 155, x + 200, 210), radius=10, fill='#F3F4F6')
    d.text((x + 100, 182), label, fill='#374151', font=font(18, bold=True), anchor='mm')
rows = [
    ('Sarah Khan', 'sarah', 'sarah@findback.ai', 'Regular User'),
    ('John Smith', 'john', 'john@findback.ai', 'Regular User'),
    ('Maya Ali', 'staff', 'staff@findback.ai', 'Staff'),
    ('Aisha Noor', 'admin', 'admin@findback.ai', 'Administrator'),
]
for i, row in enumerate(rows):
    y = 245 + i * 120
    d.rounded_rectangle((120, y, 1070, y + 80), radius=12, fill='#F9FAFB', outline='#E5E7EB')
    d.text((140, y + 40), row[0], fill='#111827', font=font(20, bold=True))
    d.text((380, y + 40), row[1], fill='#374151', font=font(18))
    d.text((580, y + 40), row[2], fill='#374151', font=font(16))
    d.text((900, y + 40), row[3], fill='#374151', font=font(18))
img.save(out_dir / 'user-management.png')

print('Generated screenshots:', sorted(p.name for p in out_dir.iterdir()))
