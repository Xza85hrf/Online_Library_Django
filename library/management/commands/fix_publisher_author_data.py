import os
import json
import re
import unicodedata
import shutil
from django.core.management.base import BaseCommand
from django.db import transaction
from library.models import Publisher, Author, Book
from django.conf import settings
from pathlib import Path


class Command(BaseCommand):
    def sanitize_author_image_filenames(self, dry_run):
        """Sanitize author image filenames to avoid invalid characters"""
        self.stdout.write("Sanitizing author image filenames...")
        
        # Get all authors
        authors = Author.objects.all()
        self.stdout.write(f"Found {authors.count()} authors")
        filenames_fixed = 0
        
        for author in authors:
            if not author.photo or not author.photo.name:
                continue
            
            # Check if the filename contains problematic characters
            current_filename = os.path.basename(author.photo.name)
            problematic_chars = [':', '?', '"', '\\', '/', '|', '*', '<', '>']
            
            if any(char in current_filename for char in problematic_chars):
                self.stdout.write(f"Author '{author.name}' has problematic characters in image filename: {current_filename}")
                
                # Create a sanitized filename
                name_parts = os.path.splitext(current_filename)
                base_name = name_parts[0]
                extension = name_parts[1] if len(name_parts) > 1 else '.jpg'
                
                # Remove problematic characters and normalize
                sanitized_base = ''
                for char in base_name:
                    if char not in problematic_chars:
                        sanitized_base += char
                    else:
                        sanitized_base += '_'
                
                # Normalize unicode characters
                sanitized_base = unicodedata.normalize('NFKD', sanitized_base).encode('ASCII', 'ignore').decode('ASCII')
                sanitized_filename = f"{sanitized_base}{extension}"
                
                if dry_run:
                    self.stdout.write(f"Would rename {current_filename} to {sanitized_filename}")
                else:
                    # Get the full paths
                    current_path = author.photo.path
                    new_path = os.path.join(os.path.dirname(current_path), sanitized_filename)
                    
                    # Check if the file exists
                    if os.path.exists(current_path):
                        try:
                            # Copy the file with the new name
                            shutil.copy2(current_path, new_path)
                            
                            # Update the author's photo field
                            new_relative_path = os.path.join(os.path.dirname(author.photo.name), sanitized_filename)
                            author.photo.name = new_relative_path
                            author.save()
                            
                            # Remove the old file if the copy was successful
                            os.remove(current_path)
                            
                            filenames_fixed += 1
                            self.stdout.write(f"Renamed {current_filename} to {sanitized_filename}")
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Error renaming {current_filename}: {e}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"File {current_path} does not exist. Updating database reference only."))
                        # Update the database reference even if the file doesn't exist
                        new_relative_path = os.path.join(os.path.dirname(author.photo.name), sanitized_filename)
                        author.photo.name = new_relative_path
                        author.save()
                        filenames_fixed += 1
                        self.stdout.write(f"Updated database reference for {current_filename} to {sanitized_filename}")
        
        self.stdout.write(f"{'Would fix' if dry_run else 'Fixed'} {filenames_fixed} author image filenames")
        return filenames_fixed
    help = 'Fixes publisher descriptions and author biographies, and removes remaining Unknown Author entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--fix-publishers',
            action='store_true',
            help='Fix publisher descriptions',
        )
        parser.add_argument(
            '--fix-authors',
            action='store_true',
            help='Fix author biographies',
        )
        parser.add_argument(
            '--fix-generic-authors',
            action='store_true',
            help='Fix generic author names like "Author of..."',
        )
        parser.add_argument(
            '--sanitize-filenames',
            action='store_true',
            help='Sanitize author image filenames to avoid invalid characters',
        )
        parser.add_argument(
            '--remove-unknown-authors',
            action='store_true',
            help='Remove remaining Unknown Author entries',
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Fix all issues (publishers, authors, generic authors, filenames, and remove Unknown Authors)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fix_publishers = options['fix_publishers'] or options['fix_all']
        fix_authors = options['fix_authors'] or options['fix_all']
        remove_unknown_authors = options['remove_unknown_authors'] or options['fix_all']
        fix_generic_authors = options['fix_generic_authors'] or options['fix_all']
        sanitize_filenames = options['sanitize_filenames'] or options['fix_all']

        if not any([fix_publishers, fix_authors, remove_unknown_authors, fix_generic_authors, sanitize_filenames]):
            self.stdout.write(self.style.WARNING(
                'No fix options specified. Use --fix-publishers, --fix-authors, --remove-unknown-authors, --fix-generic-authors, --sanitize-filenames, or --fix-all'
            ))
            return

        # Load corrections data
        corrections = self.load_corrections()

        # Start transaction
        with transaction.atomic():
            if fix_publishers:
                self.fix_publisher_descriptions(dry_run, corrections)
            
            if fix_authors:
                self.fix_author_biographies(dry_run, corrections)
            
            if remove_unknown_authors:
                self.remove_unknown_authors(dry_run)
            
            if fix_generic_authors:
                self.fix_generic_author_names(dry_run, corrections)
            
            if sanitize_filenames:
                self.sanitize_author_image_filenames(dry_run)

        if dry_run:
            self.stdout.write(self.style.SUCCESS('Dry run completed. No changes were made.'))
        else:
            self.stdout.write(self.style.SUCCESS('Publisher and author data fixes completed successfully.'))

    def load_corrections(self):
        """Load corrections from JSON file, or create default corrections if file doesn't exist"""
        corrections_path = Path(settings.BASE_DIR) / 'library' / 'data' / 'publisher_author_corrections.json'
        
        # Default corrections
        default_corrections = {
            "publishers": {
                "Oxford University Press": {
                    "description": "Oxford University Press (OUP) jest największym na świecie wydawnictwem uniwersyteckim i jednym z najstarszych, założonym w 1586 roku. Specjalizuje się w publikacjach akademickich, edukacyjnych i referencyjnych, wydając ponad 6000 tytułów rocznie w ponad 40 językach.",
                    "website": "https://global.oup.com/",
                    "founded_date": "1586-01-01"
                },
                "Kensington Publishing Corp.": {
                    "description": "Kensington Publishing Corp. to niezależne amerykańskie wydawnictwo założone w 1974 roku, specjalizujące się w literaturze popularnej, w tym romansach, thrillerach, książkach historycznych i literaturze faktu. Jest jednym z największych niezależnych wydawnictw w Stanach Zjednoczonych.",
                    "website": "https://www.kensingtonbooks.com/",
                    "founded_date": "1974-01-01"
                },
                "Houghton Mifflin Harcourt": {
                    "description": "Houghton Mifflin Harcourt (HMH) to amerykańskie wydawnictwo specjalizujące się w podręcznikach, materiałach edukacyjnych oraz literaturze dziecięcej i dorosłej. Powstało z połączenia Houghton Mifflin (zał. 1832) i Harcourt Publishing (zał. 1919) w 2007 roku.",
                    "website": "https://www.hmhco.com/",
                    "founded_date": "1832-01-01"
                }
            },
            "authors": {
                "Mark P. O. Morford": {
                    "bio": "Mark P. O. Morford był profesorem literatury klasycznej i ekspertem w dziedzinie mitologii greckiej i rzymskiej. Autor wielu publikacji akademickich, w tym bestsellerowego podręcznika 'Classical Mythology', który jest standardowym tekstem na wielu uniwersytetach. Jego prace są cenione za głęboką analizę i przystępne przedstawienie złożonych mitów klasycznych.",
                    "birth_date": "1929-01-01"
                },
                "Richard Bruce Wright": {
                    "bio": "Richard Bruce Wright (1937-2017) był kanadyjskim pisarzem, autorem powieści 'Clara Callan', która zdobyła prestiżowe nagrody literackie, w tym Giller Prize i Governor General's Award. Jego twórczość charakteryzuje się wnikliwą analizą psychologiczną postaci i osadzeniem akcji w realiach małych kanadyjskich miasteczek.",
                    "birth_date": "1937-01-01"
                },
                "Carlo D'Este": {
                    "bio": "Carlo D'Este jest amerykańskim historykiem wojskowości i byłym oficerem armii USA, specjalizującym się w II wojnie światowej. Autor wielu cenionych książek historycznych, w tym 'Decision in Normandy', 'Patton: A Genius for War' oraz biografii Winstona Churchilla. Jego prace wyróżniają się dokładnością badań i wnikliwą analizą strategii wojskowej.",
                    "birth_date": "1938-01-01"
                },
                "Gina Kolata": {
                    "bio": "Gina Kolata jest amerykańską dziennikarką naukową i pisarką, wieloletnią reporterką 'The New York Times' specjalizującą się w tematyce medycznej i naukowej. Autorka książki 'Flu: The Story of the Great Influenza Pandemic of 1918', która opisuje historię i wpływ pandemii grypy hiszpanki. Jej prace łączą rzetelność naukową z przystępnym stylem narracji.",
                    "birth_date": "1948-01-01"
                },
                "Alice Sebold": {
                    "bio": "Alice Sebold jest amerykańską pisarką, autorką bestsellerowej powieści 'The Lovely Bones' (2002), która została zekranizowana przez Petera Jacksona. Jej twórczość często porusza trudne tematy traumy i przemocy, czerpiąc częściowo z jej osobistych doświadczeń opisanych w pamiętniku 'Lucky'.",
                    "birth_date": "1963-05-06"
                },
                "Sheila Heti": {
                    "bio": "Sheila Heti jest kanadyjską pisarką i redaktorką, autorką eksperymentalnych powieści, w tym 'The Middle Stories' i 'How Should a Person Be?'. Jej twórczość łączy elementy fikcji, autobiografii i filozofii, badając granice między sztuką a życiem. Jest również współzałożycielką literackiego magazynu 'Trampoline Hall'.",
                    "birth_date": "1976-12-25"
                },
                "Victoria Helen Stone": {
                    "bio": "Victoria Helen Stone (pseudonim Victorii Dahl) jest amerykańską autorką thrillerów psychologicznych, w tym 'Jane Doe'. Jej powieści charakteryzują się silnymi kobiecymi bohaterkami, intensywną narracją i złożonymi wątkami psychologicznymi. Jej książki regularnie trafiają na listy bestsellerów i zdobywają uznanie krytyków.",
                    "birth_date": "1970-01-01"
                },
                "Loren D. Estleman": {
                    "bio": "Loren D. Estleman jest płodnym amerykańskim pisarzem, autorem ponad 80 powieści, w tym serii kryminałów o detektywie Amosie Walkerze (m.in. 'The Witchfinder'). Specjalizuje się w powieściach kryminalnych i westernach, zdobywając liczne nagrody literackie. Jego styl charakteryzuje się szczegółowymi opisami historycznymi i wyrazistymi postaciami.",
                    "birth_date": "1952-09-15"
                },
                "Robert Hendrickson": {
                    "bio": "Robert Hendrickson był amerykańskim pisarzem i leksykografem, autorem licznych książek popularnonaukowych, w tym 'More Cunning Than Man: A Social History of Rats and Man'. Specjalizował się w historii języka, etymologii i kulturowych aspektach codziennych zjawisk. Jego prace są cenione za połączenie rzetelności naukowej z przystępnym stylem.",
                    "birth_date": "1933-01-01"
                },
                "Julia Oliver": {
                    "bio": "Julia Oliver jest amerykańską pisarką z Alabamy, autorką powieści 'Goodbye to the Buttermilk Sky' oraz innych utworów osadzonych w realiach amerykańskiego Południa. Jej twórczość charakteryzuje się wnikliwym portretowaniem życia na prowincji, złożonymi postaciami kobiecymi i atmosferą nostalgii za minionymi czasami.",
                    "birth_date": "1930-01-01"
                },
                "John Grisham": {
                    "bio": "John Grisham jest jednym z najpopularniejszych amerykańskich pisarzy, autorem thrillerów prawniczych, w tym 'The Testament'. Przed karierą pisarską pracował jako prawnik, co wpłynęło na realistyczne przedstawienie świata prawniczego w jego powieściach. Jego książki sprzedały się w ponad 300 milionach egzemplarzy na całym świecie i były wielokrotnie adaptowane na filmy.",
                    "birth_date": "1955-02-08"
                },
                "Toni Morrison": {
                    "bio": "Toni Morrison (1931-2019) była amerykańską pisarką, redaktorką i profesorką, laureatką Nagrody Nobla w dziedzinie literatury (1993). Jej powieść 'Beloved' zdobyła Nagrodę Pulitzera i jest uważana za jedno z najważniejszych dzieł literatury amerykańskiej XX wieku. Jej twórczość porusza tematy rasy, tożsamości i historii Afroamerykanów, łącząc realizm z elementami magicznymi.",
                    "birth_date": "1931-02-18"
                }
            }
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(corrections_path), exist_ok=True)
        
        # If file doesn't exist, create it with default corrections
        if not os.path.exists(corrections_path):
            with open(corrections_path, 'w', encoding='utf-8') as f:
                json.dump(default_corrections, f, ensure_ascii=False, indent=4)
            self.stdout.write(f"Created default publisher and author corrections file at {corrections_path}")
            return default_corrections
        
        # Load existing corrections
        try:
            with open(corrections_path, 'r', encoding='utf-8') as f:
                corrections = json.load(f)
            self.stdout.write(f"Loaded publisher and author corrections from {corrections_path}")
            return corrections
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading corrections: {e}"))
            return default_corrections

    def fix_publisher_descriptions(self, dry_run, corrections):
        """Fix publisher descriptions that contain CSV data or are missing"""
        self.stdout.write("Fixing publisher descriptions...")
        
        # Get all publishers
        publishers = Publisher.objects.all()
        self.stdout.write(f"Found {publishers.count()} publishers")
        publishers_fixed = 0
        
        # CSV pattern to detect in descriptions
        csv_pattern = re.compile(r'Publisher of \d+;.*|^\d+;.*')
        
        for publisher in publishers:
            needs_fixing = False
            
            # Check if description contains CSV data
            if publisher.description and csv_pattern.match(publisher.description):
                needs_fixing = True
                self.stdout.write(f"Publisher '{publisher.name}' has CSV data in description")
            
            # Check if description is empty
            if not publisher.description or publisher.description.strip() == '':
                needs_fixing = True
                self.stdout.write(f"Publisher '{publisher.name}' has empty description")
            
            if needs_fixing:
                # Check if we have corrections for this publisher
                if publisher.name in corrections.get('publishers', {}):
                    publisher_data = corrections['publishers'][publisher.name]
                    
                    if dry_run:
                        self.stdout.write(f"Would update publisher '{publisher.name}' with corrected data")
                    else:
                        # Update publisher data
                        publisher.description = publisher_data.get('description', publisher.description)
                        
                        # Update website if provided and current is empty or None
                        if 'website' in publisher_data and (not publisher.website or publisher.website.strip() == ''):
                            publisher.website = publisher_data['website']
                        
                        # Update founded_date if provided and current is None
                        if 'founded_date' in publisher_data and not publisher.founded_date:
                            try:
                                from datetime import datetime
                                publisher.founded_date = datetime.strptime(publisher_data['founded_date'], '%Y-%m-%d').date()
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f"Could not parse founded_date for '{publisher.name}': {e}"))
                        
                        publisher.save()
                        publishers_fixed += 1
                        self.stdout.write(f"Updated publisher '{publisher.name}' with corrected data")
                else:
                    # Generate a generic description if no correction is available
                    if dry_run:
                        self.stdout.write(f"Would generate generic description for publisher '{publisher.name}'")
                    else:
                        # Remove CSV data if present
                        if csv_pattern.match(publisher.description or ''):
                            publisher.description = f"{publisher.name} jest wydawnictwem publikującym różnorodne tytuły literackie."
                        
                        # If description is empty, add a generic one
                        if not publisher.description or publisher.description.strip() == '':
                            publisher.description = f"{publisher.name} jest wydawnictwem publikującym różnorodne tytuły literackie."
                        
                        publisher.save()
                        publishers_fixed += 1
                        self.stdout.write(f"Generated generic description for publisher '{publisher.name}'")
        
        self.stdout.write(f"{'Would fix' if dry_run else 'Fixed'} {publishers_fixed} publishers")
        return publishers_fixed

    def fix_author_biographies(self, dry_run, corrections):
        """Fix author biographies that are missing or contain CSV data"""
        self.stdout.write("Fixing author biographies...")
        
        # Get all authors
        authors = Author.objects.all()
        self.stdout.write(f"Found {authors.count()} authors")
        authors_fixed = 0
        
        # CSV pattern to detect in biographies
        csv_pattern = re.compile(r'Author of \d+;.*|^\d+;.*')
        
        for author in authors:
            needs_fixing = False
            
            # Skip "Unknown Author" entries as they will be handled separately
            if "Unknown Author" in author.name:
                continue
            
            # Check if bio contains CSV data
            if author.bio and csv_pattern.match(author.bio):
                needs_fixing = True
                self.stdout.write(f"Author '{author.name}' has CSV data in biography")
            
            # Check if bio is empty or just "Biografia"
            if not author.bio or author.bio.strip() == '' or author.bio.strip().lower() == 'biografia':
                needs_fixing = True
                self.stdout.write(f"Author '{author.name}' has empty or generic biography")
            
            if needs_fixing:
                # Check if we have corrections for this author
                if author.name in corrections.get('authors', {}):
                    author_data = corrections['authors'][author.name]
                    
                    if dry_run:
                        self.stdout.write(f"Would update author '{author.name}' with corrected data")
                    else:
                        # Update author data
                        author.bio = author_data.get('bio', author.bio)
                        
                        # Update birth_date if provided and current is None
                        if 'birth_date' in author_data and not author.birth_date:
                            try:
                                from datetime import datetime
                                author.birth_date = datetime.strptime(author_data['birth_date'], '%Y-%m-%d').date()
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f"Could not parse birth_date for '{author.name}': {e}"))
                        
                        author.save()
                        authors_fixed += 1
                        self.stdout.write(f"Updated author '{author.name}' with corrected data")
                else:
                    # Generate a generic biography if no correction is available
                    if dry_run:
                        self.stdout.write(f"Would generate generic biography for author '{author.name}'")
                    else:
                        # Get the books by this author
                        books = Book.objects.filter(authors=author)
                        book_titles = [book.title for book in books]
                        
                        # Remove CSV data if present
                        if csv_pattern.match(author.bio or ''):
                            if book_titles:
                                author.bio = f"{author.name} jest autorem książek: {', '.join(book_titles)}."
                            else:
                                author.bio = f"{author.name} jest autorem literatury."
                        
                        # If bio is empty or just "Biografia", add a generic one
                        if not author.bio or author.bio.strip() == '' or author.bio.strip().lower() == 'biografia':
                            if book_titles:
                                author.bio = f"{author.name} jest autorem książek: {', '.join(book_titles)}."
                            else:
                                author.bio = f"{author.name} jest autorem literatury."
                        
                        author.save()
                        authors_fixed += 1
                        self.stdout.write(f"Generated generic biography for author '{author.name}'")
        
        self.stdout.write(f"{'Would fix' if dry_run else 'Fixed'} {authors_fixed} authors")
        return authors_fixed

    def remove_unknown_authors(self, dry_run):
        """Remove remaining Unknown Author entries and reassign their books to correct authors"""
        self.stdout.write("Removing remaining Unknown Author entries...")
        
        # Get all Unknown Author entries
        unknown_authors = Author.objects.filter(name__icontains="Unknown Author")
        self.stdout.write(f"Found {unknown_authors.count()} Unknown Author entries")
        
        if not unknown_authors.exists():
            self.stdout.write("No Unknown Author entries found. Skipping.")
            return 0
        
        authors_removed = 0
        
        for unknown_author in unknown_authors:
            # Get all books associated with this Unknown Author
            books = Book.objects.filter(authors=unknown_author)
            
            if not books.exists():
                # If no books are associated, just delete the Unknown Author
                if dry_run:
                    self.stdout.write(f"Would delete Unknown Author (ID: {unknown_author.id}) with no associated books")
                else:
                    unknown_author.delete()
                    authors_removed += 1
                    self.stdout.write(f"Deleted Unknown Author (ID: {unknown_author.id}) with no associated books")
                continue
            
            self.stdout.write(f"Unknown Author (ID: {unknown_author.id}) has {books.count()} associated books")
            
            # For each book, check if it has other authors
            for book in books:
                other_authors = book.authors.exclude(id=unknown_author.id)
                
                if other_authors.exists():
                    # Book has other authors, so we can safely remove the Unknown Author
                    if dry_run:
                        self.stdout.write(f"Would remove Unknown Author from book '{book.title}' (has other authors)")
                    else:
                        book.authors.remove(unknown_author)
                        self.stdout.write(f"Removed Unknown Author from book '{book.title}' (has other authors)")
                else:
                    # Book has no other authors, so we need to find a replacement
                    # Try to find an author with the same name as the book title
                    potential_authors = Author.objects.filter(name__icontains=book.title.split()[0])
                    potential_authors = potential_authors.exclude(id=unknown_author.id)
                    
                    if potential_authors.exists():
                        if dry_run:
                            self.stdout.write(f"Would replace Unknown Author with '{potential_authors[0].name}' for book '{book.title}'")
                        else:
                            book.authors.add(potential_authors[0])
                            book.authors.remove(unknown_author)
                            self.stdout.write(f"Replaced Unknown Author with '{potential_authors[0].name}' for book '{book.title}'")
                    else:
                        # Create a new generic author based on the book title
                        if dry_run:
                            self.stdout.write(f"Would create new author 'Author of {book.title}' for book '{book.title}'")
                        else:
                            new_author, created = Author.objects.get_or_create(
                                name=f"Author of {book.title}",
                                defaults={
                                    'bio': f"Autor książki '{book.title}'."
                                }
                            )
                            book.authors.add(new_author)
                            book.authors.remove(unknown_author)
                            self.stdout.write(f"Created new author '{new_author.name}' for book '{book.title}'")
            
            # Check if the Unknown Author still has any books
            if dry_run:
                self.stdout.write(f"Would check if Unknown Author (ID: {unknown_author.id}) still has books")
            else:
                remaining_books = Book.objects.filter(authors=unknown_author)
                if not remaining_books.exists():
                    unknown_author.delete()
                    authors_removed += 1
                    self.stdout.write(f"Deleted Unknown Author (ID: {unknown_author.id}) after reassigning all books")
        
        self.stdout.write(f"{'Would remove' if dry_run else 'Removed'} {authors_removed} Unknown Author entries")
        return authors_removed
        
    def fix_generic_author_names(self, dry_run, corrections):
        """Fix generic author names like 'Author of...' with real author names"""
        self.stdout.write("Fixing generic author names...")
        
        # Get all authors with names starting with 'Author of'
        generic_authors = Author.objects.filter(name__startswith="Author of")
        self.stdout.write(f"Found {generic_authors.count()} generic author names")
        
        if not generic_authors.exists():
            self.stdout.write("No generic author names found. Skipping.")
            return 0
        
        authors_fixed = 0
        book_title_to_author_mapping = {
            'The Mummies of Urumchi': 'Elizabeth Wayland Barber',
            'The Kitchen God\'s Wife': 'Amy Tan',
            'Under the Black Flag': 'David Cordingly',
            'What If?': 'Robert Cowley',
            'PLEADING GUILTY': 'Scott Turow',
            'Nights Below Station Street': 'David Adams Richards'
        }
        
        for generic_author in generic_authors:
            # Extract the book title from the author name
            book_title = generic_author.name.replace("Author of ", "")
            
            # Find the book associated with this author
            books = Book.objects.filter(authors=generic_author)
            
            if not books.exists():
                self.stdout.write(f"Generic author '{generic_author.name}' has no associated books. Skipping.")
                continue
            
            # Try to find a real author name based on the book title
            real_author_name = None
            
            # Check if we have a direct mapping for this book title
            for title_part, author_name in book_title_to_author_mapping.items():
                if title_part in book_title:
                    real_author_name = author_name
                    break
            
            # If no direct mapping, check if we have the author in our corrections
            if not real_author_name:
                for author_name, author_data in corrections.get('authors', {}).items():
                    if any(title_part in book_title for title_part in author_name.split()):
                        real_author_name = author_name
                        break
            
            if real_author_name:
                if dry_run:
                    self.stdout.write(f"Would replace generic author '{generic_author.name}' with '{real_author_name}'")
                else:
                    # Create or get the real author
                    real_author_data = corrections.get('authors', {}).get(real_author_name, {})
                    real_author, created = Author.objects.get_or_create(
                        name=real_author_name,
                        defaults={
                            'bio': real_author_data.get('bio', f"Autor książki '{book_title}'."),
                        }
                    )
                    
                    # Update birth_date if provided
                    if 'birth_date' in real_author_data and not real_author.birth_date:
                        try:
                            from datetime import datetime
                            real_author.birth_date = datetime.strptime(real_author_data['birth_date'], '%Y-%m-%d').date()
                            real_author.save()
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"Could not parse birth_date for '{real_author_name}': {e}"))
                    
                    # Reassign books from generic author to real author
                    for book in books:
                        book.authors.add(real_author)
                        book.authors.remove(generic_author)
                        self.stdout.write(f"Reassigned book '{book.title}' from '{generic_author.name}' to '{real_author_name}'")
                    
                    # Delete the generic author
                    generic_author.delete()
                    authors_fixed += 1
                    self.stdout.write(f"Replaced generic author '{generic_author.name}' with '{real_author_name}'")
            else:
                self.stdout.write(self.style.WARNING(f"Could not find a real author name for '{generic_author.name}'. Skipping."))
        
        self.stdout.write(f"{'Would fix' if dry_run else 'Fixed'} {authors_fixed} generic author names")
        return authors_fixed
