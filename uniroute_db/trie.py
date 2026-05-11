class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.room_data = None 

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str, data: dict):
        node = self.root
        word = word.lower() 
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.room_data = data

    def _collect_all_words(self, node, prefix):
        results = []
        if node.is_end_of_word:
            results.append({"name": prefix, "details": node.room_data})
            
        for char, child_node in node.children.items():
            results.extend(self._collect_all_words(child_node, prefix + char))
            
        return results

    # FUZZY (ESNEK) ARAMA FONKSİYONU
    def fuzzy_search(self, word: str, max_typos: int = 1):
        results = []
        word = word.lower()

        # Derinlik Öncelikli Arama (DFS) ile ağacı gezerken hataları sayıyoruz
        def dfs(node, current_path, target_word, index, typos):
            # Eğer hata sayısı belirlediğimiz limiti (max_typos) aşarsa o dalı aramayı bırak
            if typos > max_typos:
                return

            # Eğer kullanıcının yazdığı kelime bittiyse (veya o kadarlık kısmı eşleştiyse), altındaki her şeyi topla
            if index == len(target_word):
                results.extend(self._collect_all_words(node, current_path))
                return

            target_char = target_word[index]

            for child_char, child_node in node.children.items():
                if child_char == target_char:
                    # Harf doğruysa hata sayısını artırmadan bir alt dala geç
                    dfs(child_node, current_path + child_char, target_word, index + 1, typos)
                else:
                    # Harf YANLIŞSA hata sayısını 1 artırarak devam et (Örn: a yerine e yazılması)
                    dfs(child_node, current_path + child_char, target_word, index + 1, typos + 1)
                    # Harf EKSİKSE hata sayısını 1 artır, harfi atla (Örn: "sınıf" yerine "snıf" yazılması)
                    dfs(child_node, current_path + child_char, target_word, index, typos + 1)

        dfs(self.root, "", word, 0, 0)
        
        # Olası tekrar eden sonuçları temizleyip tekilleştiriyoruz
        unique_results = []
        seen = set()
        for r in results:
            if r["name"] not in seen:
                seen.add(r["name"])
                unique_results.append(r)
                
        return unique_results
