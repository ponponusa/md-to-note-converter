# Markdown to note.com Converter

標準的なMarkdownファイルを[note.com](https://note.com/)で利用可能な記法に変換するPythonスクリプトです。

## 特徴

- ✅ **見出しレベルの自動調整**: H1→H2、H4以降→H3に変換
- ✅ **数式記法の変換**: 標準LaTeX/Markdown数式をnote.com形式に変換
- ✅ **テーブル変換**: Markdown形式のテーブルをLaTeX array形式（数式記法）に変換
- ✅ **HTMLタグの除去**: noteで非サポートのHTMLタグを自動削除
- ✅ **YAML Front Matterの除去**: メタデータブロックを自動削除
- ✅ **詳細なレポート**: 変換時の警告やエラーを表示
- ✅ **バッチ処理**: フォルダ内の全.mdファイルを一括変換

## 変換内容

### 見出し
```markdown
# H1タイトル     → ## H2タイトル
## H2タイトル    → ## H2タイトル（変更なし）
### H3タイトル   → ### H3タイトル（変更なし）
#### H4タイトル  → ### H3タイトル
```

### 数式記法

**note.comの数式記法**:
- インライン数式: `$${数式}$$` （波括弧が必要）
- ディスプレイ数式: `$$` で囲む（別行に配置）

**変換前（標準Markdown/LaTeX）:**
```markdown
$`E = mc^2`$ や \(k_B\) といった記法

$$
F = ma
$$

または

\[
\nabla \times \mathbf{E} = -\frac{\partial \mathbf{B}}{\partial t}
\]
```

**変換後（note用）:**
```markdown
$${E = mc^2}$$ や $${k_B}$$ といった記法

$$
F = ma
$$

$$
\nabla \times \mathbf{E} = -\frac{\partial \mathbf{B}}{\partial t}
$$
```

対応する変換パターン:
- `$`...`$` → `$${...}$$` (GitHub/Markdown拡張記法)
- `\(...\)` → `$${...}$$` (LaTeX インライン)
- `\[...\]` → `$$...$$` (LaTeX ディスプレイ)
- `$...$` → `$${...}$$` (単一ドル記法)

### テーブル

**変換前（Markdown）:**
```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |
| D   | E   | F   |
```

**変換後（note用LaTeX array）:**
```markdown
$$
\begin{array}{|c|c|c|} \hline
列1 & 列2 & 列3 \\ \hline
A & B & C \\ \hline
D & E & F \\ \hline
\end{array}
$$
```

### その他
- YAML Front Matter（`---`で囲まれたメタデータ）を削除
- HTMLタグを除去（コメント含む）
- 脚注記法を検出して警告（手動対応が必要）

## インストール

依存パッケージはありません。Python 3.7以降があれば動作します。

```powershell
# リポジトリをクローン（または直接ダウンロード）
git clone <repository-url>
cd md-to-note-converter
```

## 使い方

### 基本的な使い方

```powershell
python convert_to_note.py <フォルダパス>
```

フォルダ内の全`.md`ファイルを変換し、同じフォルダに`*.note.md`として出力します。

### 使用例

```powershell
# 単一フォルダの変換
python convert_to_note.py c:\git\joke-papers\KeyDrift-Th25-001

# プレビューのみ（実際には変換しない）
python convert_to_note.py c:\git\joke-papers\KeyDrift-Th25-001 --dry-run

# 詳細なログを表示
python convert_to_note.py c:\git\joke-papers\KeyDrift-Th25-001 --verbose

# 特定のファイルを除外
python convert_to_note.py c:\git\joke-papers\KeyDrift-Th25-001 --exclude README LICENSE
```

### オプション

| オプション | 説明 |
|-----------|------|
| `--dry-run` | 実際には変換せず、プレビューのみ表示 |
| `--verbose`, `-v` | 詳細なログ（情報レベルの変換内容も表示） |
| `--exclude <パターン>` | 除外するファイル名のパターン（部分一致） |

## 出力例

```
📁 2個のMarkdownファイルを検出しました
✅ paper_ja.md → paper_ja.note.md
✅ paper_en.md → paper_en.note.md

=== 変換レポート ===

⚠️  警告 (3件):
  paper_ja.md:10 - テーブルをLaTeX array形式に変換しました（装飾は失われます）
  paper_ja.md:45 - HTMLタグを検出しました（noteでは非サポート）
  paper_en.md:120 - 脚注記法を検出しました（noteでは非サポート、手動でインライン化してください）

変換完了: 2/2個のファイル
```

## 注意事項

### テーブルの制限

noteのテーブル（LaTeX array形式）には以下の制限があります：

- ⚠️ セル内の装飾（太字、リンクなど）は失われます
- ⚠️ テーブル全体が中央配置・明朝体になります
- ⚠️ 複雑なテーブル（セル結合など）は非サポート

### 手動対応が必要な項目

以下は自動変換できないため、手動での対応が必要です：

- 📌 **画像**: 相対パスの画像は、note側で手動アップロードが必要
- 📌 **脚注**: インライン形式に手動で書き換えが必要
- 📌 **複雑なHTML**: 削除されるため、必要に応じて書き直し

## 変換フロー

```
元のMarkdown (.md)
    ↓
[変換処理]
 - YAML Front Matterを削除
 - 見出しレベルを調整
 - テーブルをLaTeX arrayに変換
 - HTMLタグを除去
 - 脚注を検出して警告
    ↓
note用Markdown (.note.md)
```

## ライセンス

MIT License

## 参考資料

- [noteヘルプ: Markdownショートカット](https://www.help-note.com/hc/ja/articles/4410617032217)
- [noteでテーブルを使用する方法](https://note.com/spr30smp/n/nd46d6ca81d93)

## トラブルシューティング

### Q: 変換後のファイルが文字化けする

A: ファイルがUTF-8エンコーディングでない可能性があります。元のファイルをUTF-8で保存し直してください。

### Q: テーブルがうまく変換されない

A: Markdown形式のテーブルが正しい形式（各行が`|`で始まり、セパレーター行がある）か確認してください。

### Q: 数式が変換されてしまう

A: `$$`や`$`で囲まれた数式記法はそのまま保持されます。変換されている場合は、元のファイルの記法を確認してください。
