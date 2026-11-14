# DUKE Pages：共通ビルド・SBOM・配備

既存の学習ダッシュボードのHTML、CSS、JavaScript、公開JSONをそのまま保持し、TECH・Voicyと同じ共通Pages処理へ接続します。学習記録の内容や評価は変更しません。

## 構成

| ファイル | 役割 |
|---|---|
| `site_adapter.py` | 公開ファイルの厳密一覧・symlink等を検査し、検証済みbytesを空stageへコピー |
| `site.json` | 公開先、必須ファイル、ブラウザで動くfirst-party assets |
| `duke_validator.py` | sandboxの既存公開検査定義をASTで抽出した固定版 |
| `duke_history.py` | 同じ既存実装の学習履歴検査定義を抽出した固定版 |
| `source-manifest.json` | 元repository/commit/path/blob/hash、抽出した定義、生成物hash |
| `../pages-core/` | 2回ビルド、tar、SBOM、schema、OSV、配備判定、HTTP照合の共通処理 |

検査の正本はsandboxの `projects/agent2/tools/learning_dashboard_release.py` と `projects/agent2/src/agent_designer/learning_dashboard_history.py` です。学習情報の公開範囲・CSP・外部通信禁止・ローカルリンク・履歴hash等の既存判定を再利用します。

抽出版は手で修正せず、sandboxの次のツールで生成します。

```sh
python3 projects/pages-release/tools/export_duke_validator.py \
  --source-root . \
  --output-directory /path/to/duke/.github/pages \
  --source-commit <正本を取得した40桁commit>
```

`--check` を付けると再生成内容との一致だけを確認します。未固定のbranch名はsource-commitに使えません。

## 動作

adapterの独立した2回の出力を比較し、同じ公開bytesから決定的tarとビルド／ブラウザの2種類のCycloneDX 1.6 SBOMを生成します。公開マーカー `_release.json` は共通coreが追加します。管理コード・SBOM・詳細証拠は公開tarへ含めません。

SBOMは固定した公式schemaを使い、外部取得なしで検証します。ビルド環境のPython packageのname/versionはOSVで照合し、不正応答、通信失敗、部分的paginationを「0件」としません。ブラウザのapp.js/style.cssはfirst-party codeとして内容hashを記録し、第三者packageの脆弱性検査とは区別します。

BuildとVerifyは読み取り用権限、DeployだけがPages/OIDC権限を持ちます。Deployでは再生成、依存インストール、checkoutを実行しません。PRでのBuild成功と、mainの本番配備成功は別の結果です。

## 初回移行

2026-11-14の確認時点ではDUKEは旧ブランチ型Pagesで、最新の [run 42898622681](https://github.com/kakurai49/duke/actions/runs/42898622681) は `dynamic/pages/pages-build-deployment` でした。mainへ本PRをマージする前に、管理者が以下を設定します。

1. `Settings → Environments → github-pages` の配備元をmainに限定する。
2. `Settings → Pages → Build and deployment → Source` を **GitHub Actions** に変更する。
3. 本PRをmainへマージし、同じcommitのBuild・Deploy・Verifyを確認する。

自動設定変更はありません。配備直前に実際のPages Sourceと `https://kakurai49.github.io/duke/` を検査し、設定が一致しない場合は止めます。GitHub連携APIが管理設定を扱えないため、この切替は管理画面で行います。

## 継続更新

学習記事を追加してもテストの件数は固定していません。公開JSONに登録された全記録とHTMLが一致することを検証します。公開ディレクトリへ原文メモや検証ファイルを追加することはできません。

app.js/style.cssを変更するときは `site.json.runtime_components` の版情報も同じ変更で更新します。現在は版番号がないfirst-partyファイルのため `sha256:<内容hash>` を使います。ライセンスを推測して付与していません。外部ライブラリやCDNを追加するときは、公開profileと依存監査の設計更新が必要です。

共通core/workflowはsandbox `projects/pages-release/` が正本です。固定commitとhashを持つvendorとして配布し、直接編集による差分はvendor検査で拒否します。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .github/pages -p 'test_*.py' -v
python3 .github/pages-core/security.py verify-vendor --root .
```

SBOM、schema、OSV、gateの全コマンドはworkflowとsandboxの設計書を参照してください。CPython/OS/ブラウザエンジン/Actionsサービスと自作コードは、PyPI packageのOSV監査で安全性を確認した対象ではありません。

## 現行保存規則による本番停止

共通基盤はsandboxの保護されたL0保存規則に従います。現在の規則はArtifactを100,000 bytes・16ファイル・保持1日に限定し、tarの送信も禁止しています。Pagesの公開tarはこの条件に適合しないため、`pages-admission` が本番upload前に拒否します。PRではuploadせず、Build・SBOM・監査・検証を実施できます。

Pages SourceをGitHub Actionsへ変更するだけでは本番公開は開通しません。sandboxの `projects/pages-release/docs/PAGES_POLICY_PROPOSAL.md` にある用途限定の改訂案について、所有者の別途承認と保護規則・検査器の新しい信頼基準が必要です。このPRは保護規則を変更しません。
