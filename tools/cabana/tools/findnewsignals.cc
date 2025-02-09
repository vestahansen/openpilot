#include <iostream>
#include <QGridLayout>
#include <QHeaderView>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QSet>
#include <QTableWidget>
#include <QTableWidgetItem>
#include <QTimer>
#include <QVector>
#include <QMap>
#include <QVBoxLayout>
#include <QDialog>
#include <QStringList>
#include <QDebug>  // For debugging purposes
#include "tools/cabana/tools/findnewsignals.h"
#include "tools/cabana/dbc/dbcmanager.h"

FindNewSignalsDlg::FindNewSignalsDlg(QWidget *parent) : QDialog(parent) {
    setWindowTitle(tr("Find New Signal"));
    setAttribute(Qt::WA_DeleteOnClose);

    QVBoxLayout *main_layout = new QVBoxLayout(this);

    QHBoxLayout *timestamp_layout = new QHBoxLayout();
    start_time_edit = new QLineEdit(this);
    start_time_edit->setPlaceholderText("Time in seconds");
    end_time_edit = new QLineEdit(this);
    end_time_edit->setPlaceholderText("Time in seconds");

    search_btn = new QPushButton(tr("&Search"), this);

    timestamp_layout->addWidget(new QLabel(tr("Start time")));
    timestamp_layout->addWidget(start_time_edit);
    timestamp_layout->addWidget(new QLabel(tr("End time")));
    timestamp_layout->addWidget(end_time_edit);
    timestamp_layout->addWidget(search_btn);

    main_layout->addLayout(timestamp_layout);

    QHBoxLayout *blacklist_layout = new QHBoxLayout();
    blacklist_edit = new QLineEdit(this);
    blacklist_edit->setPlaceholderText("Comma separated addresses to ignore");

    blacklist_layout->addWidget(new QLabel(tr("Blacklist")));
    blacklist_layout->addWidget(blacklist_edit);

    main_layout->addLayout(blacklist_layout);

    QHBoxLayout *whitelist_layout = new QHBoxLayout();
    whitelist_edit = new QLineEdit(this);
    whitelist_edit->setPlaceholderText("Comma separated addresses to allow");

    whitelist_layout->addWidget(new QLabel(tr("Whitelist")));
    whitelist_layout->addWidget(whitelist_edit);

    main_layout->addLayout(whitelist_layout);


    table = new QTableWidget(this);
    table->setSelectionBehavior(QAbstractItemView::SelectRows);
    table->setSelectionMode(QAbstractItemView::SingleSelection);
    table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    table->horizontalHeader()->setStretchLastSection(true);
    table->setSortingEnabled(true);  // Enable sorting
    main_layout->addWidget(table);

    setMinimumSize({700, 500});
    connect(search_btn, &QPushButton::clicked, this, &FindNewSignalsDlg::findNewSignals);
    connect(table->horizontalHeader(), &QHeaderView::sectionClicked, this, &FindNewSignalsDlg::sortTableByColumn);  // Connect header click to custom slot
}

void FindNewSignalsDlg::findNewSignals() {
    bool ok1;
    qint64 start_time = start_time_edit->text().toLongLong(&ok1);
    qint64 target_time = end_time_edit->text().toLongLong(&ok1);
    if (!ok1) {
        qWarning() << "Invalid time input";
        return;
    }

    const auto &events = can->allEvents();
    QMap<QPair<uint32_t, int>, int> address_counts;
    QSet<QString> messages;

    // Process blacklist
    QStringList blacklist_list = blacklist_edit->text().split(",", QString::SkipEmptyParts);
    QSet<uint32_t> blacklist;
    for (const QString &address : blacklist_list) {
        bool ok;
        uint32_t addr = address.trimmed().toUInt(&ok, 16);
        if (ok) {
            blacklist.insert(addr);
        } else {
            qWarning() << "Invalid address in blacklist:" << address;
        }
    }

    // Process whitelist
    QStringList whitelist_list = whitelist_edit->text().split(",", QString::SkipEmptyParts);
    QSet<uint32_t> whitelist;
    for (const QString &address : whitelist_list) {
        bool ok;
        uint32_t addr = address.trimmed().toUInt(&ok, 16);
        if (ok) {
            whitelist.insert(addr);
        } else {
            qWarning() << "Invalid address in whitelist:" << address;
        }
    }

    double first_time = -1.0;

    for (const CanEvent* e : events) {
        if (first_time < 0) {
            first_time = e->mono_time / 1e9;
        }

        double event_time = e->mono_time / 1e9 - first_time;
        QString data_vec = QString::number(e->address) +
                           QString(QByteArray::fromRawData(reinterpret_cast<const char*>(e->dat), e->size));

        // Check if the event is in the whitelist if whitelist is non-empty
        if (!whitelist.isEmpty() && !whitelist.contains(e->address)) {
            continue;
        }

        // Skip addresses in the blacklist
        if (blacklist.contains(e->address)) {
            continue;
        }

        if (start_time > event_time) {
            continue;
        } else if (event_time < target_time) {
            messages.insert(data_vec);
        } else if (event_time < (target_time + 1.5) && messages.find(data_vec) == messages.end()) {
            address_counts[{e->address, e->src}]++;
            messages.insert(data_vec);
        }
    }

    table->clear();
    table->setRowCount(address_counts.size());
    table->setColumnCount(4);
    table->setHorizontalHeaderLabels({"Message Name", "Address", "Bus", "Count"});

    int row = 0;
    for (auto it = address_counts.constBegin(); it != address_counts.constEnd(); ++it, ++row) {
        uint32_t address = it.key().first;
        int bus = it.key().second;
        int count = it.value();

        table->setItem(row, 0, new QTableWidgetItem(msgName({static_cast<uint8_t>(bus), address})));
        table->setItem(row, 1, new QTableWidgetItem(QString::number(address, 16)));
        table->setItem(row, 2, new QTableWidgetItem(QString::number(bus)));
        QTableWidgetItem *countItem = new QTableWidgetItem();
        countItem->setData(Qt::DisplayRole, count);
        table->setItem(row, 3, countItem);
    }
}

void FindNewSignalsDlg::sortTableByColumn(int column) {
    table->sortItems(column);
}
