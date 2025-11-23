#!/usr/bin/env python3
"""
Markdown to note.com Markdown Converter
標準的なMarkdownファイルをnoteで利用可能な記法に変換するスクリプト

Copyright (c) 2025 ponponusa
MIT License
"""

import re
import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ConversionWarning:
    """変換時の警告情報"""
    file: str
    line: int
    message: str
    severity: str  # 'info', 'warning', 'error'


class NoteMarkdownConverter:
    """Markdown → note変換クラス"""
    
    def __init__(self, verbose: bool = False):
        """コンバーターを初期化します。
        
        Args:
            verbose (bool): 詳細なログを出力するかどうか。デフォルトはFalse。
        """
        self.verbose = verbose
        self.warnings: List[ConversionWarning] = []
    
    def convert(self, content: str, filename: str = "") -> str:
        """Markdownコンテンツをnote.com用の記法に変換します。
        
        Args:
            content (str): 変換対象のMarkdownテキスト。
            filename (str): ファイル名（警告メッセージ用）。デフォルトは空文字列。
        
        Returns:
            str: note.com用に変換されたMarkdownテキスト。
        """
        # まず数式記法を変換（行処理の前に実施）
        content = self._convert_math_notation(content, filename)
        
        lines = content.split('\n')
        converted_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # YAML Front Matterの除去
            if i == 0 and line.strip() == '---':
                i = self._skip_yaml_front_matter(lines, i)
                continue
            
            # Markdownテーブルの検出と変換
            if self._is_table_line(line):
                table_lines, next_i = self._extract_table(lines, i)
                latex_table = self._convert_table_to_latex(table_lines, filename, i + 1)
                converted_lines.append(latex_table)
                i = next_i
                continue
            
            # 見出しの変換
            line = self._convert_headings(line)
            
            # HTMLタグの除去
            line = self._remove_html_tags(line, filename, i + 1)
            
            # 脚注の警告
            line = self._check_footnotes(line, filename, i + 1)
            
            converted_lines.append(line)
            i += 1
        
        return '\n'.join(converted_lines)
    
    def _skip_yaml_front_matter(self, lines: List[str], start: int) -> int:
        """YAML Front Matterをスキップし、次の処理開始位置を返します。
        
        Args:
            lines (List[str]): ファイルの全行のリスト。
            start (int): YAML Front Matterの開始位置（'---'の行番号）。
        
        Returns:
            int: YAML Front Matter終了後の次の行番号。
        """
        for i in range(start + 1, len(lines)):
            if lines[i].strip() == '---':
                self.warnings.append(ConversionWarning(
                    file="",
                    line=start + 1,
                    message="YAML Front Matterを削除しました",
                    severity="info"
                ))
                return i + 1
        return start + 1
    
    def _convert_headings(self, line: str) -> str:
        """見出しレベルをnote.com用に変換します。
        
        H1 (#) → H2 (##)
        H4以降 (####, #####, ######) → H3 (###)
        
        Args:
            line (str): 処理対象の行。
        
        Returns:
            str: 変換後の行。
        """
        # H1 (#) → H2 (##)
        if re.match(r'^# [^#]', line):
            if self.verbose:
                self.warnings.append(ConversionWarning(
                    file="",
                    line=0,
                    message="H1をH2に変換しました",
                    severity="info"
                ))
            return '#' + line
        
        # H4以降 (####, #####, ######) → H3 (###)
        match = re.match(r'^(#{4,})\s+(.+)$', line)
        if match:
            if self.verbose:
                self.warnings.append(ConversionWarning(
                    file="",
                    line=0,
                    message=f"H{len(match.group(1))}をH3に変換しました",
                    severity="info"
                ))
            return f'### {match.group(2)}'
        
        return line
    
    def _convert_math_notation(self, content: str, filename: str = "") -> str:
        r"""標準LaTeX数式記法をnote.com形式に変換します。
        
        note.comの数式記法:
        - インライン数式: $${...}$$ （波括弧が必要、全て半角）
        - ディスプレイ数式: $$ で囲む（波括弧不要、別行に配置）
        
        変換ルール:
        1. \[...\] → $$...$$（ディスプレイ数式、複数行対応）
        2. \(...\) → $${...}$$（インライン数式、複数行対応）
        3. $`...`$ → $${...}$$（GitHub/Markdown拡張記法、インライン）
        4. $...$ → $${...}$$（単一ドル記法、インライン）
        
        注意: 既存の$$...$$ブロックはそのまま保持されます。
        
        Args:
            content (str): 変換対象のMarkdownテキスト。
            filename (str): ファイル名（警告メッセージ用）。デフォルトは空文字列。
        
        Returns:
            str: 数式記法を変換後のテキスト。
        """
        original = content
        
        # 1. \[...\] をディスプレイ数式に変換（複数行対応）
        content = re.sub(
            r'\\\[\s*(.*?)\s*\\\]',
            lambda m: '$$\n' + m.group(1).strip() + '\n$$',
            content,
            flags=re.DOTALL
        )
        
        # 2. \(...\) をインライン数式に変換（複数行対応）
        content = re.sub(
            r'\\\(\s*(.*?)\s*\\\)',
            lambda m: '$${' + m.group(1).strip() + '}$$',
            content,
            flags=re.DOTALL
        )
        
        # 3. $`...`$ をインライン数式に変換（GitHub/Markdown拡張記法）
        content = re.sub(
            r'\$`([^`]+?)`\$',
            lambda m: '$${' + m.group(1).strip() + '}$$',
            content
        )
        
        # 4. $...$ をインライン数式に変換
        # $$...$$と区別するため、前後に$がないことを確認
        # また、改行を含まない単一行の数式のみ対象
        content = re.sub(
            r'(?<!\$)\$(?!\$)([^\n$]+?)\$(?!\$)',
            lambda m: '$${' + m.group(1).strip() + '}$$',
            content
        )
        
        # 5. 数式ブロック内の演算子のみの行を前の行の末尾に移動
        # note.comでは =, \le, +, - などが単独行にあると問題になる
        def fix_operator_lines(match):
            lines = match.group(0).split('\n')
            fixed_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                # 次の行をチェック
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    
                    # パターン1: 演算子のみの行（=, +, - など）
                    is_operator_only = re.match(r'^[\s]*[=≈≃+\-][\s]*$', next_line)
                    
                    # パターン2: LaTeX演算子のみの行（\le, \simeq など）
                    is_latex_operator_only = re.match(
                        r'^[\s]*\\(simeq|approx|equiv|leq|geq|neq|le|ge|ne)[\s]*$', 
                        next_line
                    )
                    
                    # パターン3: 行頭が演算子（+ M_info など）
                    starts_with_operator = re.match(r'^[\s]*[+\-]\s+\S', next_line)
                    
                    if is_operator_only or is_latex_operator_only:
                        # 演算子のみの行を現在の行の末尾に追加
                        fixed_lines.append(line.rstrip() + ' ' + next_line.strip())
                        i += 2  # 次の行をスキップ
                        continue
                    elif starts_with_operator and line.strip():
                        # 行頭の演算子を前の行の末尾に移動
                        fixed_lines.append(line.rstrip() + ' ' + next_line.strip())
                        i += 2
                        continue
                        
                fixed_lines.append(line)
                i += 1
            return '\n'.join(fixed_lines)
        
        # $$...$$ブロックに対して適用（開始$$の直後の改行はオプション）
        content = re.sub(
            r'\$\$\s*\n?(.*?)\n?\s*\$\$',
            fix_operator_lines,
            content,
            flags=re.DOTALL
        )
        
        # 変換が行われた場合、情報メッセージを追加
        if content != original and self.verbose:
            self.warnings.append(ConversionWarning(
                file=filename,
                line=0,
                message="数式記法をnote.com形式に変換しました",
                severity="info"
            ))
        
        return content
    
    def _is_table_line(self, line: str) -> bool:
        """指定された行がMarkdownテーブルの一部かどうかを判定します。
        
        Args:
            line (str): 判定対象の行。
        
        Returns:
            bool: テーブル行の場合True、それ以外はFalse。
        """
        stripped = line.strip()
        # | で始まり | で終わるか、| が2つ以上含まれる
        return bool(stripped and (stripped.startswith('|') or stripped.count('|') >= 2))
    
    def _extract_table(self, lines: List[str], start: int) -> Tuple[List[str], int]:
        """連続するテーブル行を抽出します。
        
        Args:
            lines (List[str]): ファイルの全行のリスト。
            start (int): テーブルの開始行番号。
        
        Returns:
            Tuple[List[str], int]: (抽出されたテーブル行のリスト, 次の処理開始位置)
        """
        table_lines = []
        i = start
        
        while i < len(lines) and self._is_table_line(lines[i]):
            table_lines.append(lines[i])
            i += 1
        
        return table_lines, i
    
    def _convert_table_to_latex(self, table_lines: List[str], filename: str, line_num: int) -> str:
        r"""MarkdownテーブルをLaTeX array形式（note.comの数式記法）に変換します。
        
        note.comのKaTeXテーブル仕様:
        - 列配置: l（左）, c（中央）, r（右）
        - 縦罫線なし（より読みやすいスタイル）
        - ヘッダー: 上下に実線（\hline）、改行で強調
        - データ行: 破線（\hdashline）で区切り
        
        Args:
            table_lines (List[str]): テーブルを構成する行のリスト。
            filename (str): ファイル名（警告メッセージ用）。
            line_num (int): テーブルの開始行番号（警告メッセージ用）。
        
        Returns:
            str: LaTeX array形式に変換されたテーブル文字列（$$で囲まれた形式）。
        """
        if len(table_lines) < 2:
            self.warnings.append(ConversionWarning(
                file=filename,
                line=line_num,
                message="不正な形式のテーブルです",
                severity="warning"
            ))
            return '\n'.join(table_lines)
        
        # ヘッダー行とセパレーター行を解析
        header_cells = self._parse_table_row(table_lines[0])
        
        # セパレーター行から列のアライメントを取得
        alignments = []
        if len(table_lines) > 1 and re.search(r'[-:]+', table_lines[1]):
            separator = table_lines[1]
            sep_cells = self._parse_table_row(separator)
            
            for cell in sep_cells:
                cell = cell.strip()
                if cell.startswith(':') and cell.endswith(':'):
                    alignments.append('c')  # 中央揃え
                elif cell.endswith(':'):
                    alignments.append('r')  # 右揃え
                else:
                    alignments.append('l')  # 左揃え（デフォルト）
            
            data_start = 2
        else:
            # セパレーター行がない場合はすべて左揃え
            alignments = ['l'] * len(header_cells)
            data_start = 1
        
        # 列数を決定
        num_cols = len(header_cells)
        
        # アライメント配列を列数に合わせる
        while len(alignments) < num_cols:
            alignments.append('l')
        alignments = alignments[:num_cols]
        
        # データ行を解析
        data_rows = []
        for i in range(data_start, len(table_lines)):
            cells = self._parse_table_row(table_lines[i])
            if cells:
                data_rows.append(cells)
        
        # LaTeX array形式に変換（外側に縦罫線、内側は罫線なし、読みやすいスタイル）
        col_spec = ''.join(alignments)
        
        latex_lines = ['$$', f'\\begin{{array}}{{|{col_spec}|}} \\hline']
        
        # ヘッダー行（上下に改行を入れて強調）
        # note.comのエディタでは複数行まとめて貼り付けると\がエスケープされるため、\\を出力するには\\\\と書く必要がある
        header_row = ' & '.join(self._clean_cell(cell) for cell in header_cells)
        latex_lines.append(f'\\\\\\\\{header_row} \\\\\\\\')
        latex_lines.append('\\hline \\hline')
        
        # データ行（破線で区切り）
        for i, row in enumerate(data_rows):
            # 列数を揃える
            while len(row) < num_cols:
                row.append('')
            row = row[:num_cols]
            
            data_row = ' & '.join(self._clean_cell(cell) for cell in row)
            latex_lines.append(f'{data_row} \\\\\\\\')
            
            # 最後の行は実線、それ以外は破線
            if i == len(data_rows) - 1:
                latex_lines.append('\\hline')
            else:
                latex_lines.append('\\hdashline')
        
        latex_lines.append('\\end{array}')
        latex_lines.append('$$')
        
        self.warnings.append(ConversionWarning(
            file=filename,
            line=line_num,
            message="テーブルをLaTeX array形式に変換しました（Markdownのアライメントを保持）",
            severity="info"
        ))
        
        return '\n'.join(latex_lines)
    
    def _parse_table_row(self, line: str) -> List[str]:
        """テーブル行を個別のセルに分割します。
        
        Args:
            line (str): テーブルの1行。
        
        Returns:
            List[str]: セル内容のリスト。
        """
        # 前後の | を削除
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        
        # | で分割
        cells = [cell.strip() for cell in line.split('|')]
        return cells
    
    def _clean_cell(self, cell: str) -> str:
        """テーブルセルの内容をnote.com用のLaTeX array形式に整形します。
        
        note.comのテーブル要件:
        - 数式を含むセル: $${...}$$記法を展開し、テキスト部分は\text{}で囲む
        - テキストのみのセル: \text{...}で囲む
        - 特殊文字のエスケープは最小限に
        
        Args:
            cell (str): クリーンアップ対象のセル内容。
        
        Returns:
            str: note.com用LaTeX array形式に整形されたセル内容。
        """
        # 空セルはそのまま
        if not cell.strip():
            return ''
        
        # Markdownの装飾を除去（数式の外側のみ）
        cell = re.sub(r'\*\*(.+?)\*\*', r'\1', cell)  # 太字
        cell = re.sub(r'__(.+?)__', r'\1', cell)      # 太字
        
        # リンクを除去（テキストのみ残す）
        cell = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', cell)
        
        # 数式記法を含むかチェック
        math_pattern = r'\$\$\{(.+?)\}\$\$'
        has_math = bool(re.search(math_pattern, cell))
        
        if has_math:
            # 数式とテキストが混在している可能性がある
            # 数式部分とテキスト部分を分離して処理
            parts = []
            last_end = 0
            
            for match in re.finditer(math_pattern, cell):
                # 数式の前のテキスト部分
                if match.start() > last_end:
                    text_part = cell[last_end:match.start()].strip()
                    if text_part:
                        parts.append(f'\\text{{{text_part}}}')
                
                # 数式部分（波括弧を外す）
                math_part = match.group(1)
                parts.append(math_part)
                
                last_end = match.end()
            
            # 最後の数式の後のテキスト部分
            if last_end < len(cell):
                text_part = cell[last_end:].strip()
                if text_part:
                    parts.append(f'\\text{{{text_part}}}')
            
            # 空白で結合
            return ' '.join(parts) if parts else ''
        else:
            # テキストのみの場合は\text{}で囲む
            cell = cell.strip()
            if cell and not cell.startswith('\\text{'):
                cell = f'\\text{{{cell}}}'
            return cell
    
    def _remove_html_tags(self, line: str, filename: str, line_num: int) -> str:
        """HTMLタグを検出して除去します（noteでは非サポート）。
        
        Args:
            line (str): 処理対象の行。
            filename (str): ファイル名（警告メッセージ用）。
            line_num (int): 行番号（警告メッセージ用）。
        
        Returns:
            str: HTMLタグが除去された行。
        """
        if '<' in line and '>' in line:
            # コメントは完全削除
            if '<!--' in line:
                line = re.sub(r'<!--.*?-->', '', line)
            
            # その他のHTMLタグを検出
            if re.search(r'<[^>]+>', line):
                self.warnings.append(ConversionWarning(
                    file=filename,
                    line=line_num,
                    message="HTMLタグを検出しました（noteでは非サポート）",
                    severity="warning"
                ))
                # 基本的なHTMLタグを除去（内容は保持）
                line = re.sub(r'<[^>]+>', '', line)
        
        return line
    
    def _check_footnotes(self, line: str, filename: str, line_num: int) -> str:
        """脚注記法を検出して警告を出力します（noteでは非サポート）。
        
        Args:
            line (str): 処理対象の行。
            filename (str): ファイル名（警告メッセージ用）。
            line_num (int): 行番号（警告メッセージ用）。
        
        Returns:
            str: 元の行（変更なし）。
        """
        if re.search(r'\[\^.+?\]', line):
            self.warnings.append(ConversionWarning(
                file=filename,
                line=line_num,
                message="脚注記法を検出しました（noteでは非サポート、手動でインライン化してください）",
                severity="warning"
            ))
        return line
    
    def print_warnings(self):
        """収集された警告・エラー・情報メッセージを整形して出力します。
        
        重要度別（エラー、警告、情報）に分類して表示します。
        各カテゴリーで最大10件まで表示されます。
        """
        if not self.warnings:
            return
        
        print("\n=== 変換レポート ===")
        
        # 重要度別に分類
        errors = [w for w in self.warnings if w.severity == 'error']
        warnings = [w for w in self.warnings if w.severity == 'warning']
        infos = [w for w in self.warnings if w.severity == 'info']
        
        if errors:
            print(f"\n❌ エラー ({len(errors)}件):")
            for w in errors[:10]:  # 最大10件表示
                print(f"  {w.file}:{w.line} - {w.message}")
        
        if warnings:
            print(f"\n⚠️  警告 ({len(warnings)}件):")
            for w in warnings[:10]:
                print(f"  {w.file}:{w.line} - {w.message}")
        
        if self.verbose and infos:
            print(f"\nℹ️  情報 ({len(infos)}件):")
            for w in infos[:10]:
                print(f"  {w.file}:{w.line} - {w.message}")


def process_folder(input_folder: Path, dry_run: bool = False, verbose: bool = False, exclude_patterns: Optional[List[str]] = None):
    """指定されたフォルダ内の全.mdファイルを検索して変換処理を実行します。
    
    Args:
        input_folder (Path): 処理対象のフォルダパス。
        dry_run (bool): Trueの場合、実際には変換せずプレビューのみ。デフォルトはFalse。
        verbose (bool): 詳細なログを出力するかどうか。デフォルトはFalse。
        exclude_patterns (Optional[List[str]]): 除外するファイル名のパターンリスト。デフォルトはNone。
    
    Returns:
        None
    """
    if not input_folder.exists():
        print(f"❌ エラー: フォルダが見つかりません: {input_folder}")
        sys.exit(1)
    
    if not input_folder.is_dir():
        print(f"❌ エラー: ディレクトリではありません: {input_folder}")
        sys.exit(1)
    
    # .mdファイルを検索
    md_files = list(input_folder.rglob('*.md'))
    
    # 除外パターンを適用
    if exclude_patterns:
        filtered_files = []
        for f in md_files:
            if not any(pattern in str(f) for pattern in exclude_patterns):
                filtered_files.append(f)
        md_files = filtered_files
    
    # .note.mdファイルは除外
    md_files = [f for f in md_files if not f.name.endswith('.note.md')]
    
    if not md_files:
        print(f"⚠️  {input_folder} 内に変換対象の.mdファイルが見つかりませんでした")
        return
    
    print(f"📁 {len(md_files)}個のMarkdownファイルを検出しました")
    
    converter = NoteMarkdownConverter(verbose=verbose)
    success_count = 0
    
    for md_file in md_files:
        try:
            # ファイルを読み込み
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 変換
            converted = converter.convert(content, str(md_file))
            
            # 出力ファイル名を生成
            output_file = md_file.parent / f"{md_file.stem}.note.md"
            
            if dry_run:
                print(f"[DRY-RUN] {md_file.name} → {output_file.name}")
            else:
                # ファイルに書き込み
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(converted)
                print(f"✅ {md_file.name} → {output_file.name}")
                success_count += 1
        
        except Exception as e:
            print(f"❌ エラー: {md_file.name} - {e}")
    
    # 警告レポートを表示
    converter.print_warnings()
    
    # サマリー
    print(f"\n{'[DRY-RUN] ' if dry_run else ''}変換完了: {success_count}/{len(md_files)}個のファイル")


def main():
    """コマンドライン引数をパースしてMarkdown変換処理を実行します。
    
    コマンドライン引数:
        input_folder: 変換対象の.mdファイルが含まれるフォルダパス
        --dry-run: 実際には変換せず、プレビューのみ表示
        --verbose, -v: 詳細なログを出力
        --exclude: 除外するファイル名のパターン（部分一致）
    """
    parser = argparse.ArgumentParser(
        description='Markdownファイルをnote.com用の記法に変換します',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python convert_to_note.py ./my-article
  python convert_to_note.py ./my-article --dry-run
  python convert_to_note.py ./my-article --verbose --exclude README
        """
    )
    
    parser.add_argument(
        'input_folder',
        type=Path,
        help='変換対象の.mdファイルが含まれるフォルダパス'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='実際には変換せず、プレビューのみ表示'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='詳細なログを出力'
    )
    
    parser.add_argument(
        '--exclude',
        nargs='+',
        help='除外するファイル名のパターン（部分一致）'
    )
    
    args = parser.parse_args()
    
    process_folder(
        args.input_folder,
        dry_run=args.dry_run,
        verbose=args.verbose,
        exclude_patterns=args.exclude
    )


if __name__ == '__main__':
    main()
