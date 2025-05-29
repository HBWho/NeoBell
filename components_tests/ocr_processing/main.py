from processing import process_package_label

image_file = 'package.jpg' 
package_data = process_package_label(image_file)

print(f"result: {package_data}")

if package_data:
    print("\n--- Extracted Package Data ---")
    for key, value in package_data.items():
        if key == 'raw_text' and value:
            print(f"{key}:\n{value[:300]}...") # Print only snippet of raw text
            pass # Usually too long to print fully
        elif isinstance(value, list):
            print(f"{key}:")
            for item in value:
                print(f"  - {item}")
        else:
            print(f"{key}: {value}")

    # Example of what the large DataMatrix on your label might contain:
    # Often it's a compact string with delimiters, e.g.:
    # "Recipient Name|Addr1|Addr2|City|State|CEP|Country|TRACKING_NUM|Sender Info..."
    # Or sometimes even a small JSON.
    # This needs to be investigated by printing the `barcode['data']` for DataMatrix codes.
    # For your specific image, the codes are:
    # Linear: TBR180191546
    # Large DataMatrix: Likely contains recipient address, tracking, etc.
    # Small DataMatrix codes (4 of them): Often routing or internal sorting info.
    # One of the small ones is "PBRTBR180191546" (related to the linear barcode).
    # The other three likely "GRU5", "DPR2", "CGH3C013" or similar.
