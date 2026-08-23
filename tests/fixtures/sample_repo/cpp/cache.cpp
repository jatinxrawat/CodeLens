#include <iostream>
#include <unordered_map>
#include <list>
#include <string>

/**
 * High performance Least Recently Used (LRU) Cache implementation.
 */
class LRUCache {
private:
    int capacity;
    std::list<std::pair<std::string, std::string>> items_list;
    std::unordered_map<std::string, std::list<std::pair<std::string, std::string>>::iterator> item_map;

public:
    LRUCache(int cap) : capacity(cap) {}

    /**
     * Retrieves cached value by key and moves entry to front.
     */
    std::string get(const std::string& key) {
        auto it = item_map.find(key);
        if (it == item_map.end()) {
            return "";
        }
        items_list.splice(items_list.begin(), items_list, it->second);
        return it->second->second;
    }

    /**
     * Inserts or updates key-value pair and evicts oldest element if capacity exceeded.
     */
    void put(const std::string& key, const std::string& value) {
        auto it = item_map.find(key);
        if (it != item_map.end()) {
            items_list.erase(it->second);
            item_map.erase(it);
        }
        if (items_list.size() >= capacity) {
            auto oldest = items_list.back();
            item_map.erase(oldest.first);
            items_list.pop_back();
        }
        items_list.push_front({key, value});
        item_map[key] = items_list.begin();
    }
};
