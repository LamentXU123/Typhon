# Typhon: 脳を使わずに pyjail を解くツール

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/typhonbreaker?period=total&units=ABBREVIATION&left_color=BLACK&right_color=GREEN&left_text=total%20downloads)](https://pepy.tech/projects/typhonbreaker)
![License](https://img.shields.io/badge/license-Apache_2.0-cyan.svg)
![Python_version](https://img.shields.io/pypi/pyversions/TyphonBreaker.svg?logo=python&logoColor=FBE072)
![PyPI Version](https://img.shields.io/pypi/v/TyphonBreaker)
![Tests](https://github.com/Team-intN18-SoybeanSeclab/Typhon/actions/workflows/test.yml/badge.svg)
[![codecov](https://codecov.io/gh/LamentXU123/Typhon/graph/badge.svg?token=JCH6XBAORY)](https://codecov.io/gh/LamentXU123/Typhon)

[English](./README.md), [中文](./README_CN.md), [日本語](./README_JA.md)

聞いてくれ、俺はもうあの馬鹿げたCTF pyjailの問題にうんざりだ——毎回、長いブラックリストと様々なpyjailのまとめの中から、どのチェーンがフィルタリングされていないかを探したり、名前空間で一つ一つ`dir()`を実行して使えるものを探したりするのに時間を無駄にしている。これはもう拷問だ。

だからこれがTyphon（テュポーン）だ、脳を使わずにpyjailを解くための一発勝利ツールだ。

![image](./image/usage_example.gif)

> [!IMPORTANT]
>
> **不要な時間の浪費を避けるために、使用前にドキュメントをよく読んでください：https://typhon.lamentxu.top/**

**Typhonツールを使用する前に、必ずこのREADMEを読んでください。特に[Q&A](#QA)セクションに注意してください。**

- [Highlights](#Highlights)  
- [How to Use](#How-to-Use)  
- [Q&A](#QA)
- [Proof of Concept](#Proof-of-Concept)  
- [Limitations](#Limitations)  
- [Milestones](#Milestones)  
- [Contributing](#Contributing)  
- [Credits](#Credits)  
- [License](#License)  

## Highlights

- 完全にオープンソース、無料の一発勝利ツール  
- 脳を使わずにpyjailの問題を解くことができ、脳細胞と目を守る
- 数百のガジェットとほとんどすべての主流のバイパス方法を搭載
- 様々な機能を実現するための複数の関数をサポート、例えばRCEには`bypassRCE()`、ファイル読み取りには`bypassRead()`など
- サードパーティライブラリに依存しない（CLI/WebUIを含み、すべて標準ライブラリで実装）

## How to Use

### Install

pipを使用してインストールできます：

```
pip install TyphonBreaker
```

### Step by Step Tutorial

[例のドキュメント](https://typhon.lamentxu.top/zh-cn/latest/EXAMPLE.html)の問題を通じて、Typhonの実践的な使い方を学ぶことができます。以下は単なる例です。

次のような問題があるとします：

```python
import re
def safe_run(cmd):
    if len(cmd) > 160:
        return "Command too long"
    if any([i for i in ['import', '__builtins__', '{}'] if i in cmd]):
        return "WAF!"
    if re.match(r'.*import.*', cmd):
        return "WAF!"
    exec(cmd, {'__builtins__': {}})

safe_run(input("Enter command: "))
```

**Step1. WAFの分析**

まず、pyjailのWAFの機能を分析する必要があります（これが唯一脳を使う必要がある部分かもしれません）。

上記の問題のWAFは以下の通りです：

- 長さの最大制限は160
- execの名前空間に`__builtins__`がない
- `builtins`、`import`、`{}`の文字の使用が禁止されている
- 正規表現`'.*import.*'`の制限条件が設定されている

**Step2. WAFをTyphonにインポート**

まず、exec行を削除します：

```python
import re
def safe_run(cmd):
    if len(cmd) > 160:
        return "Command too long"
    if any([i for i in ['import', '__builtins__', '{}'] if i in cmd]):
        return "WAF!"
    if re.match(r'.*import.*', cmd):
        return "WAF!"

safe_run(input("Enter command: "))
```

次に、exec行をTyphonの対応するバイパス関数に置き換え、対応する位置にWAFをインポートし、**その行の上に`import Typhon`を追加します**：

```python
import re
def safe_run(cmd):
    import Typhon
    Typhon.bypassRCE(cmd,
    banned_chr=['__builtins__', 'import', '{}'],
    banned_re='.*import.*',
    local_scope={'__builtins__': {}},
    max_length=160)

safe_run(input("Enter command: "))
```

**Step3. 実行**

問題のプログラムを実行し、**Jail broken**のメッセージが表示されるのを待ちます。

![image](./image/step-by-step-tutorial.png)

### WebUI

![image](./image/web_ui_example.png)

**方法1：コマンドラインで起動**

```
typhonbreaker webui
```

ブラウザで開く：`http://127.0.0.1:6240`

> 注：現在のWebUIは`127.0.0.1:6240`を監視しています。サーバーで実行する場合は、アクセス制御/ファイアウォールの設定に注意してください。

**方法2：Python APIで起動（現在の変数空間を注入可能）**

問題のスクリプトで直接`Typhon.webui(use_current_scope=True)`を呼び出してWebUIを起動し、
自動的に現在の`__main__`グローバル変数空間をlocal_scopeとして注入します——これはインラインの`import Typhon`の後に`Typhon.bypassRCE/bypassREAD`を実行するのと同じ効果ですが、ブラウザUIを介して操作できます。これにより、名前空間内の問題固有の変数を入力することができます。

```python
import re

def safe_run(cmd):
    if re.match(r'.*import.*', cmd):
        return "WAF!"
    import Typhon
    Typhon.webui(use_current_scope=True) # bypassRCE/bypassREADと同様
```

起動後、WebUIの"Local Scope"フィールドを空のままにすると、注入された変数空間が自動的に使用され、入力ボックスの上部に緑色の通知バナーが表示されます。
問題の`exec`が制限された名前空間（`{'__builtins__': {}}`など）を使用している場合は、UIで手動で入力する必要がまだあります。

![image](./image/local_scope_injected_banner.png)

### Docker WebUI

このリポジトリにはWebUIイメージを構築するための`Dockerfile`が含まれており、GitHub Actionsを提供してGHCRに自動的に公開しています。

1) プルして実行：

```
docker run --rm -p 6240:6240 ghcr.io/lamentxu123/typhonbreaker-webui:latest
```

2) またはcomposeを使用：

```
docker compose up --build
```

カスタムホストポート（コンテナ内はまだ6240）：

```
TYPHONBREAKER_PORT=7000 docker compose up --build
```

## Q&A

- いつ`import Typhon`を行いますか？

必ず`import Typhon`の行をTyphonの組み込みバイパス関数の直前に置いてください（たとえPEP-8強迫症であっても）。そうしないと、`Typhon`はスタックフレームを通じて現在のグローバル変数空間を取得することができません。

**推奨：**
```python
def safe_run(cmd):
    import Typhon
    Typhon.bypassRCE(cmd,
    banned_chr=['builtins', 'os', 'exec', 'import'])

safe_run('cat /f*')
```

**非推奨：**
```python
import Typhon

def safe_run(cmd):
    Typhon.bypassRCE(cmd,
    banned_chr=['builtins', 'os', 'exec', 'import'])

safe_run('cat /f*')
```

- なぜ問題と同じPythonバージョンを使用する必要があるのですか？

Pyjailには、インデックスを通じて対応するオブジェクトを見つけるガジェット（継承チェーンなど）が存在します。継承チェーンの利用はインデックスによって大きく異なります。したがって、Typhonの実行環境が問題と同じであることを必ず確認してください。

**保証できない場合？**

はい、ほとんどの問題は対応するPythonバージョンを提供しません。そのため、**Typhonはバージョン関連のガジェットを使用するときに警告を表示します**。  

![image](./image/reminder_example.png)

この場合、通常CTFプレイヤーは問題の環境でそのガジェットに必要なインデックス値を見つける必要があります。  

- 問題の`exec`と`eval`が名前空間を制限していない場合はどうしますか？

問題が名前空間を制限していない場合は、`local_scope`パラメータを入力する必要はありません。Typhonは自動的に`import Typhon`時の現在の名前空間を使用してバイパスします

- このpayloadが使えない場合、別のものに変更できますか？

パラメータに`print_all_payload=True`を追加すると、Typhonは生成したすべてのpayloadを表示します。

- このWeb問題はstdinを開いていないようで、`exec(input())`が機能しません。どうすればよいですか？

パラメータに`interactive=False`を追加すると、Typhonは`stdin`を含むすべてのpayloadの使用を禁止します。

- 最後に出力されたpayloadにエコーがない場合はどうしますか？

`bypassRCE`については、私たちは次のように考えています：**コマンドが実行されさえすれば、RCEは成功です。** エコーの問題については、リバースシェル、時間ベースのブラインドインジェクションを選択するか、`print_all_payload=True`パラメータを追加してすべてのpayloadを表示することができます。その中にエコーに成功するpayloadが含まれている可能性があります。

## Proof of Concept

Typhonの動作原理は以下の通りです：

### bypass by path & technique

私たちは2つのバイパス方法を定義しています：

- path: 異なるペイロードを通じてバイパスする（例：`os.system('calc')`と`subprocess.Popen('calc')`）  
- technique: 同じペイロードを異なる技術で処理してバイパスする（例：`os.system('c'+'a'+'l'+'c')`と`os.system('clac'[::-1])`）  

Typhonには数百のpathが組み込まれています。何かを取得するためにバイパスする必要があるたびに、まずlocal_scopeを通じて使用可能なすべての`path`を見つけ、次に`bypasser.py`の`technique`を通じて各`path`に対応する異なるバリエーションを生成し、ブラックリストをバイパスしようとします。

### gadgets chain

このアイデアは[pyjailbreaker](https://github.com/jailctf/pyjailbreaker)ツールに触発されました。

pyjailbreakerはガジェットを通じて一気にRCEを実装するのではなく、RCEチェーンに必要なアイテムを一歩一歩探します。例えば、次のようなブラックリストが存在するとします：

- ローカル名前空間に`__builtins__`がない
- `builtins`文字の使用が禁止されている

このWAFに対して、Typhonは次のように処理します：

- まず、`'J'.__class__.__class__`を通じて`type`を取得します
- 次に、typeを取得した後にbuiltinsを取得できる可能性のあるRCEチェーン`TYPE.__subclasses__(TYPE)[0].register.__globals__['__builtins__']`を見つけます
- 問題のブラックリストが`__builtins__`文字をフィルタリングしていることがわかっているので、このpathをbypasserに投入して数十のバリエーションを生成します。最も短いバリエーションを選択します：`TYPE.__subclasses__(TYPE)[0].register.__globals__['__snitliub__'[::-1]]`
- 次に、``__builtins__``を取得した後のRCEチェーン`BUILTINS_SET['breakpoint']()`を見つけます
- 最後に、builtins辞書を表すプレースホルダー`BUILTINS_SET`を前のステップで取得した`__builtins__`パスに置き換え、同様に`TYPE`プレースホルダーを実際のパスに置き換えると、最終的なpayloadが得られます。

```python
'J'.__class__.__class__.__subclasses__('J'.__class__.__class__)[0].register.__globals__['__snitliub__'[::-1]]['breakpoint']()
```

### Step by Step

Typhonのワークフローの順序は以下の通りです：

- 各エンドポイント関数（`bypassRCE`、`bypassREAD`など）は、メイン関数`bypassMAIN`を呼び出し、メイン関数は利用可能なすべてのガジェット（上記の例の`type`など）を可能な限り収集し、収集した内容を対応する下位関数に渡します。
- `bypassMAIN`関数は、現在の変数空間を簡単に分析した後、以下を実行します：
  - 直接RCEを試みる（`help()`、`breakporint()`など）
  - ジェネレータを取得しようとする
  - typeを取得しようとする
  - objectを取得しようとする
  - bytesを取得しようとする
  - 現在の空間の``__builtins__``が削除されていないが変更されている場合は、回復しようとする（`id.__self__`など）
  - 現在の空間の``__builtins__``が削除されている場合は、他の名前空間から回復しようとする
  - 続けて、継承チェーンのバイパスを試みる
  - importパッケージの能力を取得しようとする
  - 回復された可能性のある``__builtins__``を通じて直接RCEを試みる
  - 結果を下位関数に渡す
- 下位関数は`bypassMAIN`の結果を受け取った後、その関数が実装する要件に応じて、対応するガジェットを選択して処理します（`bypassRCE`はRCEに焦点を当て、`bypassREAD`はファイル読み取りに焦点を当て、`bypassENV`は環境変数の読み取りに焦点を当てます）。そのプロセスは上記と同様です。

具体的な実装プロセスについては、ブログを参照してください：https://www.cnblogs.com/LAMENTXU/articles/19101758

## Limitations

- 現在、TyphonはPython 3.9以上のバージョンのみをサポートしています。
- 現在、TyphonはLinuxサンドボックスのみをサポートしています。
- 現在、Typhonはaudithookサンドボックスをバイパスすることができません。
- Typhonは局所的に最適な再帰戦略を採用しているため、いくつかの単純な問題に対しては、むしろ時間がかかる場合があります（約1分）。
- 現在知られているサポートされていないバイパス方法：

  - Typhonは`list[0]`の代わりに`list.pop(0)`をサポートしていません。これは、Typhonが生成するすべてのpayloadが有効であることを確認するためにローカル実行で検証する必要があり、`pop`メソッドは検証時にリストから要素を削除し、後続の環境を破壊するためです。

## Milestones

### v1.0（リリース済み）

- [x] 基本フレームワークの実装

### v1.1

- [ ] より多くのバイパス器の実装
    - [x] マジックメソッドを使用して二項演算子を置き換える（`a+b`の代わりに`a.__add__(b)`）
    - [ ] `list[0]`の代わりに`list.pop(0)`
    - [x] `'a'`の代わりに`list(dict(a=1))[0]`
    - [x] 空文字列を`str()`で置き換える
- [ ] 組み込みのbashバイパス器の実装
- [x] より良い`bypassREAD`関数  
- [x] ホワイトリスト機能の実装
- [x] `bytes`の自動検索

### v1.2

- [ ] `audithook`サンドボックスのバイパスの実装  
- [ ] 長さ制限がない場合、局所的に長さ最適な再帰アルゴリズムを使用しない
- [ ] 環境変数の読み取りのための`bypassENV`関数の実装

## Contributing

### Typhonで解けない問題を提供する

私たちはTyphonで解けない問題を長期的に収集しています。これはツールのパフォーマンスを向上させるために非常に重要です！一発勝利できない問題に遭遇した場合は、このリポジトリでissueを開き、問題の出典（できれば対応する解法）を記載してください。私たちは可能な限りその問題の自動解決を実装します。

見返りとして、次のリリースバージョンにあなたのGitHub IDを含めます。

## Credits

**Author & Maintainer**

@ [LamentXU (Weilin Du)](https://github.com/LamentXU123)  

**Contributors**

このプロジェクトに貢献したすべての方々に感謝します：

<a href="https://github.com/eryajf/learn-github/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Team-intN18-SoybeanSeclab/Typhon" />
</a>

**Copyright**

bashバイパスのための組み込みバイパス器については、[bashFuck](https://github.com/ProbiusOfficial/bashFuck)プロジェクトの作者@ [ProbiusOfficial](https://github.com/ProbiusOfficial)に感謝します。その[License](https://github.com/ProbiusOfficial/bashFuck/blob/main/README.md)はこちらです。

Copyright (c) 2024 ProbiusOfficial.

下流のプロジェクト（ある場合）は必ずこれを含めてください。

注：現在のバージョンにはこの機能はまだ追加されていません。この著作権情報は事前に予約されています。

**Special Thanks**

@ [黄豆安全实验室](https://hdsec.cn)には必要な励ましを与えていただきました  
@ [pyjailbreaker](https://github.com/jailctf/pyjailbreaker)プロジェクトには私にインスピレーションを与えていただきました  

## License

このプロジェクトは[Apache 2.0](https://github.com/LamentXU123/Typhon/blob/main/LICENSE)ライセンスの下でリリースされています。

Copyright (c) 2025 Weilin Du.

## 404星链计划
<img src="https://github.com/knownsec/404StarLink/raw/master/Images/logo.png" width="30%">

Typhonは[404星链计划](https://github.com/knownsec/404StarLink)に参加しています

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Team-intN18-SoybeanSeclab/Typhon&type=Date&theme=dark" />
  <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Team-intN18-SoybeanSeclab/Typhon&type=Date" />
  <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Team-intN18-SoybeanSeclab/Typhon&type=Date" />
</picture>