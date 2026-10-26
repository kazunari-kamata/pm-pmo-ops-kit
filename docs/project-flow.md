# プロジェクトフローとガントチャート

この図は、テンプレートを使う工程の全体像を示す架空の例です。案件の規模、契約、組織の規程に合わせて、工程・期間・承認者を調整してください。

## 工程フロー

```mermaid
flowchart TB
    startNode([構想・立上げ]) --> charter[プロジェクト憲章を合意]
    charter --> requirements[要件定義]
    requirements --> reqReview{"要件・受入条件を合意?"}
    reqReview -->|いいえ| requirements
    reqReview -->|はい| planning[計画策定]
    planning --> planReview{"体制・WBS・リスクを承認?"}
    planReview -->|いいえ| planning
    planReview -->|はい| delivery[設計・開発]
    delivery --> testing[テスト・受入]
    testing --> acceptance{"受入条件を満たす?"}
    acceptance -->|いいえ| delivery
    acceptance -->|はい| release[移行・リリース]
    release --> closure[終結・振り返り]
    closure --> completeNode([完了])

    raid[(RAID・変更管理)] -.-> requirements
    raid -.-> planning
    raid -.-> delivery
    raid -.-> testing
    decisions[(意思決定ログ)] -.-> reqReview
    decisions -.-> planReview
    decisions -.-> acceptance
```

工程ゲートでは、合意済みの事項だけでなく、条件付き承認の条件、未解決事項、判断者、判断日を[意思決定ログ](../templates/decision-log.md)に残します。スコープ・品質・費用・日程・体制に影響する変更は、実施前に[RAID・変更管理台帳](../templates/raid-change-log.md)で影響評価します。

## 標準的な進行イメージ

```mermaid
gantt
    title プロジェクト進行イメージ（架空の12週間例）
    dateFormat  YYYY-MM-DD
    axisFormat  %m/%d

    section 立上げ
    憲章・体制・キックオフ       :done, init, 2027-01-04, 5d

    section 要件・計画
    要件定義・合意               :crit, req, after init, 15d
    WBS・RAID・連絡計画          :plan, after req, 5d

    section 実行
    設計・開発・レビュー          :build, after plan, 25d
    テスト計画・受入準備          :testplan, after plan, 10d
    テスト・受入                  :crit, test, after build, 10d

    section 移行・終結
    移行・リリース                :milestone, release, after test, 0d
    完了報告・振り返り            :close, after release, 5d
```

このガントチャートは説明用の基準線です。実際の計画では、WBSを基準に成果物、担当、依存関係、節目、完了条件を定義し、進捗報告では基準線との差異と対処案を示します。

## 定例での管理サイクル

```mermaid
flowchart LR
    collect[実績・課題・リスクを収集] --> assess[影響と優先度を評価]
    assess --> decide{"判断・承認が必要?"}
    decide -->|はい| escalate[判断依頼・エスカレーション]
    decide -->|いいえ| action[担当と期限を設定]
    escalate --> action
    action --> report[進捗報告・台帳を更新]
    report --> collect
```

定例では、状態の報告だけで終わらせず、次に必要な判断、担当者、期限を確定します。重大な差異は、[コミュニケーション計画](../templates/communication-plan.md)で定めた経路と期限に従ってエスカレーションします。
