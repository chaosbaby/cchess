#!/usr/bin/env python3
"""
XQF to DXQ/TXT converter.
Correctly implements XQF 1.0/1.1/1.2+ decryption and tree traversal.
Supports extraction of match info, player names, and variations (branches).
Supports recursive directory traversal and structure preservation.
Supports external configuration via JSON and CLI arguments.
"""

import os
import sys
import argparse
import json
from pathlib import Path

# Defaults
DEFAULT_VER = "ss孤街漫步"
DEFAULT_AUTHOR = "" # No default for author
DEFAULT_GENERATOR = "新月飞鹰"

def calculate_keys(data):
    if len(data) < 16:
        return None
    
    version = data[2]
    key_mask = data[3]
    key_or_a = data[8]
    key_or_b = data[9]
    key_or_c = data[10]
    key_or_d = data[11]
    keys_sum = data[12]
    key_xy = data[13]
    key_xyf = data[14]
    key_xyt = data[15]
    
    b1 = (keys_sum & key_mask) | key_or_a
    b2 = (key_xy & key_mask) | key_or_b
    b3 = (key_xyf & key_mask) | key_or_c
    b4 = (key_xyt & key_mask) | key_or_d
    
    char_list = [
        '[', '(', 'C', ')', ' ', 'C', 'o', 'p', 'y', 'r', 'i', 'g', 'h', 't', ' ', 'M',
        'r', '.', ' ', 'D', 'o', 'n', 'g', ' ', 'S', 'h', 'i', 'w', 'e', 'i', '.', ']'
    ]
    bytes_arr = [b1, b2, b3, b4]
    f32_keys = []
    for i in range(32):
        f32_keys.append(ord(char_list[i]) & bytes_arr[i % 4])
        
    def calc_k(bk, seed):
        return (((((bk * bk) * 3 + 9) * 3 + 8) * 2 + 1) * 3 + 8) * seed
            
    if version <= 10:
        s_key_xy = 0
        s_key_xyf = 0
        s_key_xyt = 0
        s_key_rmk_size = 0
    else:
        s_key_xy = calc_k(key_xy, key_xy) % 256
        s_key_xyf = calc_k(key_xyf, s_key_xy) % 256
        s_key_xyt = calc_k(key_xyt, s_key_xyf) % 256
        w_key = (keys_sum * 256) + key_xy
        s_key_rmk_size = (w_key % 32000) + 767
        
    return {
        'version': version,
        'f32_keys': f32_keys,
        's_key_xy': s_key_xy,
        's_key_xyf': s_key_xyf,
        's_key_xyt': s_key_xyt,
        's_key_rmk_size': s_key_rmk_size
    }

def decrypt_byte(b, pos, f32_keys):
    return (b - f32_keys[pos % 32]) % 256

def extract_string(data, offset, length):
    """Extract a Pascal-style or NULL-terminated string from data."""
    if len(data) < offset + length:
        return ""
    
    chunk = data[offset : offset + length]
    
    p_len = chunk[0]
    if 0 < p_len < length:
        try:
            return chunk[1 : 1 + p_len].rstrip(b'\x00').decode('gbk').strip()
        except:
            pass
    
    try:
        null_pos = chunk.find(b'\x00')
        if null_pos != -1:
            return chunk[:null_pos].decode('gbk').strip()
        return chunk.decode('gbk').strip()
    except:
        return ""

def get_binit(data, keys):
    s_key_xy = keys['s_key_xy']
    version = keys['version']
    
    qizi_xy_raw = data[16:48]
    rearranged = [0] * 32
    
    for i_0 in range(32):
        if version >= 12:
            target_0 = (i_0 + 1 + s_key_xy) % 32
            rearranged[target_0] = qizi_xy_raw[i_0]
        else:
            rearranged[i_0] = qizi_xy_raw[i_0]
            
    final_qizi = []
    for val in rearranged:
        dec = (val - s_key_xy) % 256
        if dec > 89:
            final_qizi.append(99)
        else:
            final_qizi.append(dec)
            
    binit_parts = final_qizi[16:32] + final_qizi[0:16]
    return "".join(f"{v:02d}" for v in binit_parts)

class XQFParser:
    def __init__(self, data):
        self.data = data
        self.keys = calculate_keys(data)
        self.pos = 0
        self.branches = {0: {'parent': -1, 'start': 0, 'moves': []}}
        self.comments = {} # (branch_id, move_idx) -> text
        self.branch_count = 0
        
    def parse(self):
        if not self.keys: return
        
        ptree_pos = int.from_bytes(self.data[56:60], "little")
        if ptree_pos == 0:
            ptree_pos = 1024
        
        self.pos = ptree_pos
        self.traverse(branch_id=0, move_idx=0)
        
    def traverse(self, branch_id, move_idx):
        if self.pos + 4 > len(self.data):
            return

        xyf_enc = self.data[self.pos]
        xyt_enc = self.data[self.pos + 1]
        tag_enc = self.data[self.pos + 2]
        
        xyf_dec = decrypt_byte(xyf_enc, self.pos, self.keys['f32_keys'])
        xyt_dec = decrypt_byte(xyt_enc, self.pos + 1, self.keys['f32_keys'])
        tag_dec = decrypt_byte(tag_enc, self.pos + 2, self.keys['f32_keys'])
        
        self.pos += 4
        
        remark_size = 0
        if self.keys['version'] <= 10:
            if self.pos + 4 <= len(self.data):
                rmk_enc = self.data[self.pos : self.pos + 4]
                rmk_dec = bytearray([decrypt_byte(rmk_enc[i], self.pos + i, self.keys['f32_keys']) for i in range(4)])
                remark_size = int.from_bytes(rmk_dec, "little")
                self.pos += 4
        else:
            if (tag_dec & 0x20) != 0:
                if self.pos + 4 <= len(self.data):
                    rmk_enc = self.data[self.pos : self.pos + 4]
                    rmk_dec = bytearray([decrypt_byte(rmk_enc[i], self.pos + i, self.keys['f32_keys']) for i in range(4)])
                    remark_size = int.from_bytes(rmk_dec, "little")
                    self.pos += 4
            tag_dec = tag_dec & 0xE0
            
        if move_idx != 0:
            f_pos_xqf = (xyf_dec - 24 - self.keys['s_key_xyf']) % 256
            t_pos_xqf = (xyt_dec - 32 - self.keys['s_key_xyt']) % 256
            
            f_x, f_y = f_pos_xqf // 10, f_pos_xqf % 10
            t_x, t_y = t_pos_xqf // 10, t_pos_xqf % 10
            f_pos_dxq = f_x * 10 + (9 - f_y)
            t_pos_dxq = t_x * 10 + (9 - t_y)
            
            self.branches[branch_id]['moves'].append(f"{f_pos_dxq:02d}{t_pos_dxq:02d}")
                
        if remark_size > 0:
            real_size = remark_size - self.keys['s_key_rmk_size']
            if real_size > 0 and self.pos + real_size <= len(self.data):
                comment_data = bytearray([decrypt_byte(self.data[self.pos + i], self.pos + i, self.keys['f32_keys']) for i in range(real_size)])
                try:
                    comment_text = comment_data.rstrip(b'\x00').decode('gbk', errors='replace').strip()
                    if comment_text:
                        self.comments[(branch_id, move_idx)] = comment_text
                except:
                    pass
                self.pos += real_size
                
        if (tag_dec & 0x80) != 0:
            self.traverse(branch_id, move_idx + 1)
            
        if (tag_dec & 0x40) != 0:
            new_branch_id = self.branch_count + 1
            self.branch_count = new_branch_id
            self.branches[new_branch_id] = {'parent': branch_id, 'start': move_idx - 1, 'moves': []}
            self.traverse(new_branch_id, move_idx)

def xqf_to_dxq(xqf_path, output_path=None, encoding='gb2312', ver=None, author=None, generator=None):
    with open(xqf_path, "rb") as f:
        data = f.read()
        
    parser = XQFParser(data)
    parser.parse()
    
    # Priority: Extracted from XQF > CLI Param/Config > Default
    title = extract_string(data, 80, 64)
    event = extract_string(data, 208, 64)
    date = extract_string(data, 272, 16)
    place = extract_string(data, 288, 16)
    red = extract_string(data, 304, 16)
    black = extract_string(data, 320, 16)
    
    # Author Priority: Parse > CLI/Config > None
    xqf_author = extract_string(data, 480, 16)
    final_author = xqf_author or author or DEFAULT_AUTHOR
    
    binit = get_binit(data, parser.keys)
    
    dxq_parts = [
        "[DhtmlXQ]",
        f"[DhtmlXQ_ver]{ver or DEFAULT_VER}[/DhtmlXQ_ver]",
        f"[DhtmlXQ_title]{title}[/DhtmlXQ_title]",
        f"[DhtmlXQ_event]{event}[/DhtmlXQ_event]",
        f"[DhtmlXQ_date]{date}[/DhtmlXQ_date]",
        f"[DhtmlXQ_place]{place}[/DhtmlXQ_place]",
        "[DhtmlXQ_round][/DhtmlXQ_round]",
        "[DhtmlXQ_table][/DhtmlXQ_table]",
        f"[DhtmlXQ_red]{red}[/DhtmlXQ_red]",
        "[DhtmlXQ_redteam][/DhtmlXQ_redteam]",
        f"[DhtmlXQ_black]{black}[/DhtmlXQ_black]",
        "[DhtmlXQ_blackteam][/DhtmlXQ_blackteam]",
        f"[DhtmlXQ_author]{final_author}[/DhtmlXQ_author]",
        f"[DhtmlXQ_binit]{binit}[/DhtmlXQ_binit]",
    ]

    main_moves = "".join(parser.branches[0]['moves'])
    dxq_parts.append(f"[DhtmlXQ_movelist]{main_moves}[/DhtmlXQ_movelist]")

    for b_id in sorted(parser.branches.keys()):
        if b_id == 0: continue
        branch = parser.branches[b_id]
        p_id = branch['parent']
        start_idx = branch['start']
        moves = "".join(branch['moves'])
        if moves:
            dxq_parts.append(f"[DhtmlXQ_move_{p_id}_{start_idx}_{b_id}]{moves}[/DhtmlXQ_move_{p_id}_{start_idx}_{b_id}]")

    for (b_id, m_idx), text in sorted(parser.comments.items()):
        tag = f"DhtmlXQ_comment{m_idx}" if b_id == 0 else f"DhtmlXQ_comment{b_id}_{m_idx}"
        dxq_parts.append(f"[{tag}]{text}[/{tag}]")

    dxq_parts.extend([
        "[DhtmlXQ_type]实战全局/开局[/DhtmlXQ_type]",
        "[DhtmlXQ_timerule][/DhtmlXQ_timerule]",
        f"[DhtmlXQ_generator]{generator or DEFAULT_GENERATOR}[/DhtmlXQ_generator]",
        "[/DhtmlXQ]",
    ])

    dxq = "\n".join(dxq_parts)

    if output_path:
        with open(output_path, "w", encoding=encoding, errors='replace') as f:
            f.write(dxq)

    return dxq

def load_config():
    """Load config from xqf_to_txt.json in the script's directory."""
    script_dir = Path(__file__).parent.resolve()
    config_path = script_dir / "xqf_to_txt.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}", file=sys.stderr)
    return {}

def main():
    config = load_config()
    
    parser = argparse.ArgumentParser(description="XQF to DXQ converter")
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("-o", "--output", help="Output directory or file")
    parser.add_argument("-e", "--encoding", help=f"Output file encoding (default from config or gb2312)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursively traverse directories")
    parser.add_argument("--ver", help=f"Value for DhtmlXQ_ver (default: {DEFAULT_VER})")
    parser.add_argument("--author", help=f"Value for DhtmlXQ_author")
    parser.add_argument("--gen", help=f"Value for DhtmlXQ_generator (default: {DEFAULT_GENERATOR})")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")

    args = parser.parse_args()

    # Priority: CLI > JSON Config > Hardcoded Defaults
    input_path = Path(args.input)
    enc = args.encoding or config.get("encoding", "gb2312")
    ver = args.ver or config.get("ver", DEFAULT_VER)
    author = args.author or config.get("author", DEFAULT_AUTHOR)
    gen = args.gen or config.get("gen", DEFAULT_GENERATOR)
    recursive = args.recursive or config.get("recursive", False)
    
    if enc.lower() == 'unicode':
        enc = 'utf-16'
    
    if input_path.is_dir():
        output_root = Path(args.output or input_path)
        files_to_process = []
        if recursive:
            for root, dirs, files in os.walk(input_path):
                for f in files:
                    if f.lower().endswith(".xqf"):
                        files_to_process.append(Path(root) / f)
        else:
            for f in input_path.iterdir():
                if f.is_file() and f.suffix.lower() == ".xqf":
                    files_to_process.append(f)
                    
        for xqf_path in sorted(files_to_process):
            rel_path = xqf_path.relative_to(input_path)
            txt_path = (output_root / rel_path).with_suffix(".txt")
            if not args.dry_run:
                txt_path.parent.mkdir(parents=True, exist_ok=True)

            if args.dry_run:
                print(f"[Would generate] {txt_path} (enc: {enc}, ver: {ver}, gen: {gen})")
            else:
                xqf_to_dxq(str(xqf_path), str(txt_path), encoding=enc, ver=ver, author=author, generator=gen)
                print(f"[Generated] {txt_path}")
    else:
        if args.dry_run:
            dxq = xqf_to_dxq(str(input_path), encoding=enc, ver=ver, author=author, generator=gen)
            print(dxq)
        else:
            output_path = args.output or str(input_path.with_suffix(".txt"))
            xqf_to_dxq(str(input_path), output_path, encoding=enc, ver=ver, author=author, generator=gen)
            print(f"[Generated] {output_path}")

if __name__ == "__main__":
    main()
